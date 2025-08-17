from typing import Dict, Any
from utils.utils import to_tags, derive_is_remote, parse_salary
from configs.settings import settings
from da.dao import Job
from datetime import datetime

def clean_job(raw: Dict[str, Any]) -> Job:
    title = (raw.get("title") or "").strip()
    company = (raw.get("company") or "").strip()
    location = (raw.get("location") or "").strip()
    salary = (raw.get("salary") or None)
    tags = to_tags(raw.get("tags") or [])
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")
    currency = raw.get("currency")
    if salary and (salary_min is None or salary_max is None):
        salary_min, salary_max, currency = parse_salary(salary)

    is_remote = raw.get("is_remote")
    if is_remote is None:
        is_remote = derive_is_remote(title, location, tags)

    return Job(
        source=raw["source"],
        mode=raw.get("mode", "dynamic"),
        title=title,
        company=company,
        location=location or None,
        salary=salary,
        salary_min=salary_min,
        salary_max=salary_max,
        currency=currency,
        tags=tags,
        posted_date=raw.get("posted_date") or datetime.utcnow(),
        job_url=raw["job_url"],
        is_remote=is_remote,
    )
