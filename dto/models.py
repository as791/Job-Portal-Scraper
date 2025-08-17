"""
DTO (Data Transfer Object) models for API responses.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class JobResponse(BaseModel):
    """Response model for job data."""
    source: str = Field(..., description="Job source (linkedin, naukri)")
    mode: str = Field(..., description="Scraping mode (static, dynamic)")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    salary: Optional[str] = Field(None, description="Salary information")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    currency: Optional[str] = Field(None, description="Salary currency")
    tags: List[str] = Field(default=[], description="Job tags")
    posted_date: datetime = Field(..., description="Job posted date")
    job_url: HttpUrl = Field(..., description="Job URL")
    is_remote: bool = Field(..., description="Whether job is remote")


class JobSearchResponse(BaseModel):
    """Response model for job search."""
    total_jobs: int = Field(..., description="Total number of jobs found")
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    search_time: float = Field(..., description="Search time in seconds")
    timestamp: datetime = Field(..., description="Search timestamp")
    pagination: dict = Field(..., description="Pagination information")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database_connected: bool = Field(..., description="Database connection status")
    scrapers_available: List[str] = Field(..., description="Available scrapers")
