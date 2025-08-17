"""
MongoDB database handler for job scraping application.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from da.dao import Job, JobTag, JobTagStats
from configs.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBHandler:
    """MongoDB database handler for job data management."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.jobs_collection: Optional[Collection] = None
        self.jobs_tag_collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(settings.mongodb_uri)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[settings.mongodb_db]
            self.jobs_collection = self.db[settings.jobs_collection]
            self.jobs_tag_collection = self.db[settings.tags_collection]
            
            # Create indexes for better performance
            self._create_indexes()
            
            logger.info("MongoDB connection established", 
                       database=settings.mongodb_db,
                       jobs_collection=settings.jobs_collection,
                       tags_collection=settings.tags_collection)
            
        except ConnectionFailure as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise
    
    def _create_indexes(self) -> None:
        """Create database indexes for optimal performance."""
        try:
            # Jobs collection indexes
            # Create compound unique index on source and job_url
            self.jobs_collection.create_index([("source", 1), ("job_url", 1)], unique=True)
            
            # Remove old single field unique index if it exists
            try:
                self.jobs_collection.drop_index("job_url_1")
            except:
                pass  # Index doesn't exist
            
            # Individual indexes for better query performance
            self.jobs_collection.create_index([("title", 1)])
            self.jobs_collection.create_index([("company", 1)])
            self.jobs_collection.create_index([("location", 1)])
            self.jobs_collection.create_index([("posted_date", -1)])
            self.jobs_collection.create_index([("source", 1)])
            self.jobs_collection.create_index([("tags", 1)])
            self.jobs_collection.create_index([("is_remote", 1)])
            
            # Jobs tag collection indexes
            self.jobs_tag_collection.create_index([("tag", 1)], unique=True)
            self.jobs_tag_collection.create_index([("count", -1)])
            self.jobs_tag_collection.create_index([("category", 1)])
            self.jobs_tag_collection.create_index([("created_at", -1)])
            self.jobs_tag_collection.create_index([("updated_at", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error("Failed to create indexes", error=str(e))
    
    def insert_job(self, job: Job) -> bool:
        """Insert a single job into the database."""
        try:
            job_dict = job.model_dump()
            # Convert HttpUrl to string for MongoDB compatibility
            if 'job_url' in job_dict and hasattr(job_dict['job_url'], '__str__'):
                job_dict['job_url'] = str(job_dict['job_url'])
            job_dict["created_at"] = datetime.utcnow()
            
            self.jobs_collection.insert_one(job_dict)
            
            # Update tag counts for this job
            self._update_job_tags(job.tags)
            
            logger.info("Job inserted successfully", job_id=str(job_dict.get("_id")))
            return True
            
        except DuplicateKeyError:
            logger.warning("Job already exists", source=job.source, job_url=job.job_url)
            return False
        except Exception as e:
            logger.error("Failed to insert job", error=str(e), job_url=job.job_url)
            return False
    
    def insert_jobs_bulk(self, jobs: List[Job]) -> int:
        """Insert multiple jobs in bulk."""
        try:
            job_dicts = []
            all_tags = set()
            
            for job in jobs:
                job_dict = job.model_dump()
                # Convert HttpUrl to string for MongoDB compatibility
                if 'job_url' in job_dict and hasattr(job_dict['job_url'], '__str__'):
                    job_dict['job_url'] = str(job_dict['job_url'])
                job_dict["created_at"] = datetime.utcnow()
                job_dicts.append(job_dict)
                all_tags.update(job.tags)
            
            result = self.jobs_collection.insert_many(job_dicts, ordered=False)
            inserted_count = len(result.inserted_ids)
            
            # Update tag counts for all jobs
            self._update_job_tags_bulk(list(all_tags))
            
            logger.info("Bulk jobs insertion completed", 
                       inserted_count=inserted_count,
                       total_count=len(jobs))
            return inserted_count
            
        except Exception as e:
            logger.error("Failed to insert jobs in bulk", error=str(e))
            return 0
    
    def _update_job_tags(self, tags: List[str]) -> None:
        """Update tag counts when a job is inserted."""
        try:
            for tag in tags:
                if tag.strip():
                    self.jobs_tag_collection.update_one(
                        {"tag": tag.strip().lower()},
                        {
                            "$inc": {"count": 1},
                            "$setOnInsert": {
                                "created_at": datetime.utcnow(),
                                "category": self._categorize_tag(tag)
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        },
                        upsert=True
                    )
        except Exception as e:
            logger.error("Failed to update job tags", error=str(e))
    
    def _update_job_tags_bulk(self, tags: List[str]) -> None:
        """Update tag counts for multiple tags efficiently."""
        try:
            for tag in tags:
                if tag.strip():
                    self.jobs_tag_collection.update_one(
                        {"tag": tag.strip().lower()},
                        {
                            "$inc": {"count": 1},
                            "$setOnInsert": {
                                "created_at": datetime.utcnow(),
                                "category": self._categorize_tag(tag)
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        },
                        upsert=True
                    )
        except Exception as e:
            logger.error("Failed to update job tags in bulk", error=str(e))
    
    def _categorize_tag(self, tag: str) -> str:
        """Categorize a tag based on its content."""
        tag_lower = tag.lower()
        
        # Technology tags
        tech_keywords = ['python', 'java', 'javascript', 'react', 'node', 'aws', 'docker', 'kubernetes', 'sql', 'nosql']
        if any(keyword in tag_lower for keyword in tech_keywords):
            return 'technology'
        
        # Experience level tags
        exp_keywords = ['senior', 'junior', 'entry', 'lead', 'principal', 'architect']
        if any(keyword in tag_lower for keyword in exp_keywords):
            return 'experience'
        
        # Location tags
        location_keywords = ['remote', 'onsite', 'hybrid', 'india', 'us', 'uk', 'canada']
        if any(keyword in tag_lower for keyword in location_keywords):
            return 'location'
        
        # Job type tags
        job_type_keywords = ['full-time', 'part-time', 'contract', 'internship', 'freelance']
        if any(keyword in tag_lower for keyword in job_type_keywords):
            return 'job_type'
        
        return 'other'
    
    def get_job_by_url(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Get a job by its URL."""
        try:
            job = self.jobs_collection.find_one({"job_url": job_url})
            return job
        except Exception as e:
            logger.error("Failed to get job by URL", error=str(e), job_url=job_url)
            return None
    
    def get_jobs_by_query(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs matching a search query."""
        try:
            # Text search across title, company, and tags
            pipeline = [
                {
                    "$search": {
                        "text": {
                            "query": query,
                            "path": ["title", "company", "tags"]
                        }
                    }
                },
                {"$limit": limit},
                {"$sort": {"posted_date": -1}}
            ]
            
            jobs = list(self.jobs_collection.aggregate(pipeline))
            logger.info("Jobs retrieved by query", query=query, count=len(jobs))
            return jobs
            
        except Exception as e:
            logger.error("Failed to get jobs by query", error=str(e), query=query)
            return []
    
    def get_jobs_count(self,
                      query: Optional[str] = None,
                      source: Optional[str] = None,
                      company: Optional[str] = None,
                      location: Optional[str] = None,
                      is_remote: Optional[bool] = None) -> int:
        """Get total count of jobs matching filters."""
        try:
            filter_query = {}
            if query:
                filter_query["title"] = {"$regex": query, "$options": "i"}
            if source:
                filter_query["source"] = source
            if company:
                filter_query["company"] = {"$regex": company, "$options": "i"}
            if location and location.strip():  # Check if location is not empty
                filter_query["location"] = {"$regex": location.strip(), "$options": "i"}
            if is_remote is not None:
                filter_query["is_remote"] = is_remote
            
            count = self.jobs_collection.count_documents(filter_query)
            logger.info("Jobs count retrieved", filters=filter_query, count=count)
            return count
            
        except Exception as e:
            logger.error("Failed to get jobs count", error=str(e))
            return 0
    
    def get_jobs_by_filters(self, 
                          query: Optional[str] = None,
                          source: Optional[str] = None,
                          company: Optional[str] = None,
                          location: Optional[str] = None,
                          is_remote: Optional[bool] = None,
                          tags: Optional[List[str]] = None,
                          limit: int = 50,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """Get jobs with filters including tags."""
        try:
            filter_query = {}
            if query:
                filter_query["title"] = {"$regex": query, "$options": "i"}
            if source:
                filter_query["source"] = source
            if company:
                filter_query["company"] = {"$regex": company, "$options": "i"}
            if location and location.strip():  # Check if location is not empty
                filter_query["location"] = {"$regex": location.strip(), "$options": "i"}
            if is_remote is not None:
                filter_query["is_remote"] = is_remote
            if tags and len(tags) > 0:  # Check if tags list is not empty
                filter_query["tags"] = {"$in": [tag.lower() for tag in tags if tag.strip()]}
            
            jobs = list(self.jobs_collection.find(filter_query)
                       .sort("posted_date", -1)
                       .skip(offset)
                       .limit(limit))
            
            logger.info("Jobs retrieved with filters", 
                       filters=filter_query, 
                       count=len(jobs))
            return jobs
            
        except Exception as e:
            logger.error("Failed to get jobs with filters", error=str(e))
            return []
    
    def update_job_tags(self, job_url: str, tags: List[str]) -> bool:
        """Update tags for a specific job."""
        try:
            # Get old tags first
            old_job = self.jobs_collection.find_one({"job_url": job_url})
            if old_job:
                old_tags = old_job.get("tags", [])
                
                # Decrement old tag counts
                for tag in old_tags:
                    self.jobs_tag_collection.update_one(
                        {"tag": tag.lower()},
                        {"$inc": {"count": -1}, "$set": {"updated_at": datetime.utcnow()}}
                    )
            
            # Update job with new tags
            result = self.jobs_collection.update_one(
                {"job_url": job_url},
                {"$set": {"tags": tags, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                # Increment new tag counts
                self._update_job_tags(tags)
                logger.info("Job tags updated", job_url=job_url, tags=tags)
                return True
            return False
            
        except Exception as e:
            logger.error("Failed to update job tags", error=str(e), job_url=job_url)
            return False
    
    def get_job_tag(self, tag: str) -> Optional[JobTag]:
        """Get a specific job tag."""
        try:
            tag_doc = self.jobs_tag_collection.find_one({"tag": tag.lower()})
            if tag_doc:
                return JobTag(**tag_doc)
            return None
        except Exception as e:
            logger.error("Failed to get job tag", error=str(e), tag=tag)
            return None
    
    def get_popular_tags(self, limit: int = 20, category: Optional[str] = None) -> List[JobTag]:
        """Get most popular job tags with optional category filter."""
        try:
            filter_query = {}
            if category:
                filter_query["category"] = category
            
            pipeline = [
                {"$match": filter_query},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            tags = list(self.jobs_tag_collection.aggregate(pipeline))
            job_tags = [JobTag(**tag) for tag in tags]
            
            logger.info("Popular tags retrieved", count=len(job_tags), category=category)
            return job_tags
            
        except Exception as e:
            logger.error("Failed to get popular tags", error=str(e))
            return []
    
    def get_tags_by_category(self) -> Dict[str, List[JobTag]]:
        """Get all tags grouped by category."""
        try:
            pipeline = [
                {"$group": {"_id": "$category", "tags": {"$push": "$$ROOT"}}},
                {"$sort": {"_id": 1}}
            ]
            
            categories = list(self.jobs_tag_collection.aggregate(pipeline))
            result = {}
            
            for cat in categories:
                category_name = cat["_id"] or "uncategorized"
                tags = [JobTag(**tag) for tag in cat["tags"]]
                result[category_name] = sorted(tags, key=lambda x: x.count, reverse=True)
            
            logger.info("Tags by category retrieved", categories=list(result.keys()))
            return result
            
        except Exception as e:
            logger.error("Failed to get tags by category", error=str(e))
            return {}
    
    def get_recent_tags(self, days: int = 7, limit: int = 10) -> List[JobTag]:
        """Get recently added tags."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            tags = list(self.jobs_tag_collection.find({
                "created_at": {"$gte": cutoff_date}
            }).sort("created_at", -1).limit(limit))
            
            job_tags = [JobTag(**tag) for tag in tags]
            logger.info("Recent tags retrieved", count=len(job_tags), days=days)
            return job_tags
            
        except Exception as e:
            logger.error("Failed to get recent tags", error=str(e))
            return []
    
    def get_job_tag_statistics(self) -> JobTagStats:
        """Get comprehensive job tag statistics."""
        try:
            # Total tags
            total_tags = self.jobs_tag_collection.count_documents({})
            
            # Most popular tags
            popular_tags = self.get_popular_tags(limit=10)
            
            # Tags by category
            tags_by_category = self.get_tags_by_category()
            
            # Recent tags
            recent_tags = self.get_recent_tags(days=7, limit=5)
            
            # Calculate growth rate (tags added in last 7 days vs previous 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            two_weeks_ago = datetime.utcnow() - timedelta(days=14)
            
            recent_count = self.jobs_tag_collection.count_documents({"created_at": {"$gte": week_ago}})
            previous_count = self.jobs_tag_collection.count_documents({
                "created_at": {"$gte": two_weeks_ago, "$lt": week_ago}
            })
            
            growth_rate = (recent_count - previous_count) / max(previous_count, 1) * 100
            
            stats = JobTagStats(
                total_tags=total_tags,
                most_popular_tags=popular_tags,
                tags_by_category=tags_by_category,
                recent_tags=recent_tags,
                tag_growth_rate=growth_rate
            )
            
            logger.info("Job tag statistics retrieved", total_tags=total_tags)
            return stats
            
        except Exception as e:
            logger.error("Failed to get job tag statistics", error=str(e))
            return JobTagStats()
    
    def search_tags(self, query: str, limit: int = 10) -> List[JobTag]:
        """Search for tags by name."""
        try:
            tags = list(self.jobs_tag_collection.find({
                "tag": {"$regex": query, "$options": "i"}
            }).sort("count", -1).limit(limit))
            
            job_tags = [JobTag(**tag) for tag in tags]
            logger.info("Tags searched", query=query, count=len(job_tags))
            return job_tags
            
        except Exception as e:
            logger.error("Failed to search tags", error=str(e), query=query)
            return []
    
    def update_tag_metadata(self, tag: str, category: Optional[str] = None, synonyms: Optional[List[str]] = None) -> bool:
        """Update tag metadata like category and synonyms."""
        try:
            update_data = {"updated_at": datetime.utcnow()}
            if category is not None:
                update_data["category"] = category
            if synonyms is not None:
                update_data["synonyms"] = synonyms
            
            result = self.jobs_tag_collection.update_one(
                {"tag": tag.lower()},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info("Tag metadata updated", tag=tag, category=category)
                return True
            return False
            
        except Exception as e:
            logger.error("Failed to update tag metadata", error=str(e), tag=tag)
            return False
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics."""
        try:
            total_jobs = self.jobs_collection.count_documents({})
            remote_jobs = self.jobs_collection.count_documents({"is_remote": True})
            
            # Get jobs by source
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            jobs_by_source = list(self.jobs_collection.aggregate(pipeline))
            
            # Get recent jobs (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_jobs = self.jobs_collection.count_documents({"posted_date": {"$gte": week_ago}})
            
            stats = {
                "total_jobs": total_jobs,
                "remote_jobs": remote_jobs,
                "recent_jobs": recent_jobs,
                "jobs_by_source": jobs_by_source
            }
            
            logger.info("Job statistics retrieved", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get job statistics", error=str(e))
            return {}
    
    def cleanup_old_jobs(self, days_old: int = 90) -> int:
        """Remove jobs older than specified days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Get old jobs to update tag counts
            old_jobs = list(self.jobs_collection.find({"posted_date": {"$lt": cutoff_date}}))
            
            # Decrement tag counts for old jobs
            for job in old_jobs:
                for tag in job.get("tags", []):
                    self.jobs_tag_collection.update_one(
                        {"tag": tag.lower()},
                        {"$inc": {"count": -1}, "$set": {"updated_at": datetime.utcnow()}}
                    )
            
            # Delete old jobs
            result = self.jobs_collection.delete_many({"posted_date": {"$lt": cutoff_date}})
            
            logger.info("Old jobs cleaned up", 
                       deleted_count=result.deleted_count, 
                       cutoff_date=cutoff_date)
            return result.deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup old jobs", error=str(e))
            return 0
    
    def create_source_job_url_index(self) -> bool:
        """Manually create the compound unique index on source and job_url."""
        try:
            # Drop existing index if it exists
            try:
                self.jobs_collection.drop_index("source_1_job_url_1")
            except:
                pass  # Index doesn't exist
            
            # Create the compound unique index
            self.jobs_collection.create_index([("source", 1), ("job_url", 1)], unique=True)
            logger.info("Compound unique index created on source and job_url")
            return True
            
        except Exception as e:
            logger.error("Failed to create compound unique index", error=str(e))
            return False
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

