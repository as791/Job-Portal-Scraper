from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field

class Job(BaseModel):
    source: str
    mode: str
    title: str
    company: str
    location: str | None = None
    salary: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    tags: List[str] = []
    posted_date: datetime
    job_url: HttpUrl
    is_remote: bool = False


class JobTag(BaseModel):
    """Individual job tag model."""
    tag: str = Field(..., description="Tag name")
    count: int = Field(default=0, description="Number of jobs with this tag")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When tag was first created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When tag was last updated")
    category: Optional[str] = Field(default=None, description="Tag category (e.g., 'technology', 'location', 'experience')")
    synonyms: List[str] = Field(default=[], description="Alternative names for this tag")


class JobTagStats(BaseModel):
    """Job tag statistics model."""
    total_tags: int = Field(default=0, description="Total number of unique tags")
    most_popular_tags: List[JobTag] = Field(default=[], description="Most popular tags")
    tags_by_category: dict = Field(default={}, description="Tags grouped by category")
    recent_tags: List[JobTag] = Field(default=[], description="Recently added tags")
    tag_growth_rate: float = Field(default=0.0, description="Tag growth rate over time")
