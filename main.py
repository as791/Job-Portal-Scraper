#!/usr/bin/env python3
"""
Job Scraper CLI Application.
Provides command-line interface for job scraping and data management.
"""
import argparse
import json
import sys
from datetime import datetime
from typing import List, Optional

from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.naukri_scraper import NaukriScraper
from da.database import MongoDBHandler
from da.dao import Job
from utils.logger import setup_logging, get_logger


# Setup logging
setup_logging()
logger = get_logger(__name__)


class JobScraperCLI:
    """CLI application for job scraping."""
    
    def __init__(self):
        self.db_handler = None
        try:
            self.db_handler = MongoDBHandler()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database not available: {e}")
    
    def scrape_static(self, query: str, source: Optional[str], company: Optional[str], 
                     location: Optional[str], is_remote: Optional[bool], limit: int, offset: int = 0) -> List[dict]:
        """Search jobs from MongoDB database (static mode)."""
        if not self.db_handler:
            logger.error("Database not available for static search")
            return []
        
        try:
            # Build filters
            filters = {}
            if query:
                filters["title"] = {"$regex": query, "$options": "i"}
            if company:
                filters["company"] = {"$regex": company, "$options": "i"}
            if source:
                filters["source"] = source
            if is_remote is not None:
                filters["is_remote"] = is_remote
            
            # Get jobs from database
            jobs_data = self.db_handler.get_jobs_by_filters(
                query=query,
                source=source,
                company=company,
                location=location,
                is_remote=is_remote,
                tags=None,
                limit=limit,
                offset=offset
            )
            
            logger.info(f"Found {len(jobs_data)} jobs from database")
            return jobs_data
            
        except Exception as e:
            logger.error(f"Static search failed: {e}")
            return []
    
    def scrape_dynamic(self, query: str, source: Optional[str], company: Optional[str], 
                      location: Optional[str], is_remote: Optional[bool], limit: int) -> List[dict]:
        """Live scraping from job sites (dynamic mode)."""
        jobs = []
        saved_count = 0
        
        # Determine sources to scrape
        sources_to_scrape = ["linkedin"]
        if source:
            if source == "naukri":
                sources_to_scrape = ["naukri"]
            elif source == "linkedin":
                sources_to_scrape = ["linkedin"]
        
        # Use company and query as query if provided both else if company not provided then query and else if query not provided then company 
        search_query = company + " " + query if company and query else company or query
        
        for source_name in sources_to_scrape:
            try:
                if source_name == "linkedin":
                    scraper = LinkedInScraper()
                    try:
                        scraped_jobs = list(scraper.scrape(search_query, limit, location))
                        jobs.extend(scraped_jobs)
                        logger.info(f"LinkedIn scraping completed: {len(scraped_jobs)} jobs")
                        
                        # Save to MongoDB
                        if scraped_jobs:
                            try:
                                saved_jobs = self.db_handler.insert_jobs_bulk(scraped_jobs)
                                saved_count += len(saved_jobs)
                                logger.info(f"Saved {len(saved_jobs)} LinkedIn jobs to MongoDB")
                            except Exception as e:
                                logger.error(f"Failed to save LinkedIn jobs to MongoDB: {e}")
                    finally:
                        scraper.close()
                
                elif source_name == "naukri":
                    scraper = NaukriScraper()
                    try:
                        scraped_jobs = list(scraper.scrape(search_query, limit, location))
                        jobs.extend(scraped_jobs)
                        logger.info(f"Naukri scraping completed: {len(scraped_jobs)} jobs")
                        
                        # Save to MongoDB
                        if scraped_jobs:
                            try:
                                saved_jobs = self.db_handler.insert_jobs_bulk(scraped_jobs)
                                saved_count += len(saved_jobs)
                                logger.info(f"Saved {len(saved_jobs)} Naukri jobs to MongoDB")
                            except Exception as e:
                                logger.error(f"Failed to save Naukri jobs to MongoDB: {e}")
                    finally:
                        scraper.close()
                        
            except Exception as e:
                logger.error(f"Dynamic scraping failed for {source_name}: {e}")
        
        logger.info(f"Dynamic scraping completed: {len(jobs)} total jobs, {saved_count} saved to MongoDB")
        return jobs
    
    def export_jobs(self, jobs: List[dict], output_file: str):
        """Export jobs to JSON file."""
        try:
            # Convert MongoDB ObjectId and datetime to string for JSON serialization
            serializable_jobs = []
            for job in jobs:
                job_copy = job.copy()
                # Convert ObjectId to string if present
                if '_id' in job_copy:
                    job_copy['_id'] = str(job_copy['_id'])
                # Convert datetime to ISO string if present
                if 'posted_date' in job_copy and job_copy['posted_date']:
                    job_copy['posted_date'] = job_copy['posted_date'].isoformat()
                if 'created_at' in job_copy and job_copy['created_at']:
                    job_copy['created_at'] = job_copy['created_at'].isoformat()
                if 'updated_at' in job_copy and job_copy['updated_at']:
                    job_copy['updated_at'] = job_copy['updated_at'].isoformat()
                serializable_jobs.append(job_copy)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(jobs)} jobs to {output_file}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
    
    def serve_api(self):
        """Start the FastAPI server."""
        try:
            import uvicorn
            logger.info("Starting FastAPI server...")
            uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
    
    def display_jobs(self, jobs: List[dict], limit: int = 10):
        """Display jobs in a formatted way."""
        if not jobs:
            print("No jobs found.")
            return
        
        print(f"\nFound {len(jobs)} jobs:")
        print("=" * 80)
        
        for i, job in enumerate(jobs[:limit], 1):
            print(f"{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Source: {job.get('source', 'N/A')}")
            print(f"   Remote: {job.get('is_remote', False)}")
            print(f"   URL: {job.get('job_url', 'N/A')}")
            print("-" * 80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Job Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py scrape-static --query "python" --location "Bengaluru" --limit 10
  python main.py scrape-dynamic --source linkedin --company "Google" --limit 5
  python main.py export --query "software" --location "Mumbai" --output jobs.json
  python main.py serve
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Common arguments for scraping
    def add_common_args(subparser):
        subparser.add_argument('--query', default='software engineer', 
                              help='Search query (default: software engineer)')
        subparser.add_argument('--source', choices=['linkedin', 'naukri'], 
                              help='Source to scrape from')
        subparser.add_argument('--company', help='Company filter')
        subparser.add_argument('--location', help='Location filter')
        subparser.add_argument('--is-remote', type=bool, help='Remote work filter (true/false)')
        subparser.add_argument('--limit', type=int, default=100, 
                              help='Maximum number of jobs (default: 100, max: 1000)')
        subparser.add_argument('--offset', type=int, default=0, 
                              help='Number of jobs to skip for pagination (default: 0)')
    
    # scrape-static command
    static_parser = subparsers.add_parser('scrape-static', 
                                         help='Search jobs from MongoDB database')
    add_common_args(static_parser)
    
    # scrape-dynamic command
    dynamic_parser = subparsers.add_parser('scrape-dynamic', 
                                          help='Live scraping from job sites')
    add_common_args(dynamic_parser)
    
    # export command
    export_parser = subparsers.add_parser('export', 
                                         help='Export jobs to JSON file')
    add_common_args(export_parser)
    export_parser.add_argument('--output', default=f'jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                               help='Output file name')
    export_parser.add_argument('--mode', choices=['static', 'dynamic'], default='static',
                               help='Export mode (default: static)')
    
    # serve command
    serve_parser = subparsers.add_parser('serve', 
                                        help='Start FastAPI server')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Validate limit (only if limit is provided)
    if hasattr(args, 'limit') and args.limit and args.limit > 1000:
        print("Error: Limit cannot exceed 1000")
        sys.exit(1)
    
    # Initialize CLI
    cli = JobScraperCLI()
    
    try:
        if args.command == 'scrape-static':
            jobs = cli.scrape_static(
                query=args.query,
                source=args.source,
                company=args.company,
                location=args.location,
                is_remote=args.is_remote,
                limit=args.limit,
                offset=args.offset
            )
            cli.display_jobs(jobs, args.limit)
            
        elif args.command == 'scrape-dynamic':
            jobs = cli.scrape_dynamic(
                query=args.query,
                source=args.source,
                company=args.company,
                location=args.location,
                is_remote=args.is_remote,
                limit=args.limit
            )
            cli.display_jobs(jobs, args.limit)
            
        elif args.command == 'export':
            if args.mode == 'static':
                jobs = cli.scrape_static(
                    query=args.query,
                    source=args.source,
                    company=args.company,
                    location=args.location,
                    is_remote=args.is_remote,
                    limit=args.limit,
                    offset=args.offset
                )
            else:  # dynamic
                jobs = cli.scrape_dynamic(
                    query=args.query,
                    source=args.source,
                    company=args.company,
                    location=args.location,
                    is_remote=args.is_remote,
                    limit=args.limit
                )
            
            cli.export_jobs(jobs, args.output)
            print(f"Exported {len(jobs)} jobs to {args.output}")
            
        elif args.command == 'serve':
            cli.serve_api()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"CLI operation failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
