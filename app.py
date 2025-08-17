#!/usr/bin/env python3
"""
FastAPI application for job scraping.
Provides simplified REST API endpoints for job search.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Literal
import time
from datetime import datetime

from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.naukri_scraper import NaukriScraper
from da.database import MongoDBHandler
from da.dao import Job
from utils.logger import setup_logging, get_logger
from dto.models import JobResponse, JobSearchResponse, HealthResponse


# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Job Scraper API",
    description="Simplified REST API for job scraping",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database handler
db_handler = None
try:
    db_handler = MongoDBHandler()
    logger.info("Database connection established for API")
except Exception as e:
    logger.warning(f"Database not available for API: {e}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database_connected=db_handler is not None,
        scrapers_available=["linkedin", "naukri"]
    )


@app.get("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query for job title"),
    company: Optional[str] = Query(None, description="Company filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    source: Optional[str] = Query(None, description="Source filter (linkedin, naukri)"),
    mode: Literal["static", "dynamic"] = Query("static", description="Search mode"),
    remote: Optional[bool] = Query(None, alias="is_remote", description="Remote work filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip for pagination")
):
    """
    Search jobs with filters.
    
    - static: Search from MongoDB database
    - dynamic: Live scraping from job sites
    """
    start_time = time.time()
    
    try:
        if mode == "static":
            # Search from database
            if not db_handler:
                raise HTTPException(status_code=503, detail="Database not available")
            
            # Get total count for pagination
            total_count = db_handler.get_jobs_count(
                query=query,
                source=source,
                company=company,
                location=location,
                is_remote=remote
            )
            
            # Get jobs from database with pagination
            jobs_data = db_handler.get_jobs_by_filters(
                query=query,
                source=source,
                company=company,
                location=location,
                is_remote=remote,
                tags=None,  # Not used in this simplified version
                limit=limit,
                offset=offset
            )
            
            # Convert to response format
            jobs = []
            for job_data in jobs_data:
                try:
                    job_response = JobResponse(
                        source=job_data.get("source", ""),
                        mode="static",
                        title=job_data.get("title", ""),
                        company=job_data.get("company", ""),
                        location=job_data.get("location", ""),
                        salary=job_data.get("salary"),
                        salary_min=job_data.get("salary_min"),
                        salary_max=job_data.get("salary_max"),
                        currency=job_data.get("currency"),
                        tags=job_data.get("tags", []),
                        posted_date=job_data.get("posted_date"),
                        job_url=job_data.get("job_url", ""),
                        is_remote=job_data.get("is_remote", False)
                    )
                    jobs.append(job_response)
                except Exception as e:
                    logger.warning(f"Failed to create job response: {e}")
                    continue
            
        else:  # dynamic mode
            # Live scraping
            jobs = []
            # For dynamic mode, we don't support pagination - ignore offset
            
            # Determine sources to scrape
            sources_to_scrape = ["linkedin"]
            if source:
                if source == "naukri":
                    sources_to_scrape = ["naukri"]
                elif source == "linkedin":
                    sources_to_scrape = ["linkedin"]
                # If source is None, use default (linkedin)
            
            # Scrape from each source
            for source_name in sources_to_scrape:
                if source_name == "linkedin":
                    scraper = LinkedInScraper()
                    try:
                        # Use company as query if provided, otherwise use a default
                        query = company if company else "software engineer"
                        scraped_jobs = list(scraper.scrape(query, limit, location))
                        
                        # Save to MongoDB
                        if scraped_jobs:
                            try:
                                db_handler.insert_jobs_bulk(scraped_jobs)
                                logger.info(f"Saved {len(scraped_jobs)} LinkedIn jobs to MongoDB")
                            except Exception as e:
                                logger.error(f"Failed to save LinkedIn jobs to MongoDB: {e}")
                        
                        for job_data in scraped_jobs:
                            try:
                                job_response = JobResponse(
                                    source=job_data.get("source", ""),
                                    mode="dynamic",
                                    title=job_data.get("title", ""),
                                    company=job_data.get("company", ""),
                                    location=job_data.get("location", ""),
                                    salary=job_data.get("salary"),
                                    salary_min=job_data.get("salary_min"),
                                    salary_max=job_data.get("salary_max"),
                                    currency=job_data.get("currency"),
                                    tags=job_data.get("tags", []),
                                    posted_date=job_data.get("posted_date"),
                                    job_url=job_data.get("job_url", ""),
                                    is_remote=job_data.get("is_remote", False)
                                )
                                jobs.append(job_response)
                            except Exception as e:
                                logger.warning(f"Failed to create job response: {e}")
                                continue
                    finally:
                        scraper.close()
                
                elif source_name == "naukri":
                    scraper = NaukriScraper()
                    try:
                        query = company if company else "software"
                        scraped_jobs = list(scraper.scrape(query, limit, location))
                        
                        # Save to MongoDB
                        if scraped_jobs:
                            try:
                                db_handler.insert_jobs_bulk(scraped_jobs)
                                logger.info(f"Saved {len(scraped_jobs)} Naukri jobs to MongoDB")
                            except Exception as e:
                                logger.error(f"Failed to save Naukri jobs to MongoDB: {e}")
                        
                        for job_data in scraped_jobs:
                            try:
                                job_response = JobResponse(
                                    source=job_data.get("source", ""),
                                    mode="dynamic",
                                    title=job_data.get("title", ""),
                                    company=job_data.get("company", ""),
                                    location=job_data.get("location", ""),
                                    salary=job_data.get("salary"),
                                    salary_min=job_data.get("salary_min"),
                                    salary_max=job_data.get("salary_max"),
                                    currency=job_data.get("currency"),
                                    tags=job_data.get("tags", []),
                                    posted_date=job_data.get("posted_date"),
                                    job_url=job_data.get("job_url", ""),
                                    is_remote=job_data.get("is_remote", False)
                                )
                                jobs.append(job_response)
                            except Exception as e:
                                logger.warning(f"Failed to create job response: {e}")
                                continue
                    finally:
                        scraper.close()
        
        search_time = time.time() - start_time
        
        # Calculate pagination info
        if mode == "static":
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
            current_page = (offset // limit) + 1 if offset > 0 else 1
            has_next = offset + limit < total_count
            has_previous = offset > 0
            total_jobs = total_count
        else:  # dynamic mode
            # Dynamic mode doesn't support pagination
            total_pages = 1
            current_page = 1
            has_next = False
            has_previous = False
            total_jobs = len(jobs)
        
        pagination_info = {
            "total_jobs": total_jobs,
            "current_page": current_page,
            "total_pages": total_pages,
            "limit": limit,
            "offset": offset if mode == "static" else 0,  # Ignore offset for dynamic mode
            "has_next": has_next,
            "has_previous": has_previous
        }
        
        return JobSearchResponse(
            total_jobs=len(jobs),
            jobs=jobs,
            search_time=search_time,
            timestamp=datetime.utcnow(),
            pagination=pagination_info
        )
        
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
