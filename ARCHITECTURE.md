# Job Scraper - System Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Component Diagram](#component-diagram)
4. [Data Flow](#data-flow)
5. [API Architecture](#api-architecture)
6. [Database Design](#database-design)
7. [Scraping Engine](#scraping-engine)
8. [Deployment Architecture](#deployment-architecture)
9. [Security & Rate Limiting](#security--rate-limiting)
10. [Error Handling](#error-handling)
11. [Performance Considerations](#performance-considerations)

## System Overview

The Job Scraper is a multi-layered application designed for scalable job data extraction and management. It follows a clean architecture pattern with clear separation of concerns.

### Core Principles
- **Separation of Concerns**: Each layer has a specific responsibility
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each component has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Testability**: All components are easily testable

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface (main.py)  │  REST API (app.py)             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  JobScraperCLI  │  FastAPI Endpoints  │  Business Logic    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Scrapers  │  Data Models  │  DTOs  │  Utilities          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
├─────────────────────────────────────────────────────────────┤
│  MongoDB  │  Selenium  │  Rate Limiting  │  Logging        │
└─────────────────────────────────────────────────────────────┘
```

## Component Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI[CLI Interface<br/>main.py]
        API[REST API<br/>app.py]
    end
    
    subgraph "Application Layer"
        CLI_Handler[JobScraperCLI]
        API_Handler[FastAPI Handlers]
        Business[Business Logic]
    end
    
    subgraph "Domain Layer"
        BaseScraper[BaseScraper<br/>Abstract Class]
        LinkedInScraper[LinkedIn Scraper]
        NaukriScraper[Naukri Scraper]
        JobModel[Job Model<br/>Pydantic]
        JobTagModel[JobTag Model<br/>Pydantic]
        DTOs[DTO Models<br/>API Responses]
        Utils[Utility Functions]
    end
    
    subgraph "Infrastructure Layer"
        MongoDB[(MongoDB<br/>Database)]
        Selenium[Selenium<br/>WebDriver]
        RateLimiter[Token Bucket<br/>Rate Limiter]
        Logger[Structured<br/>Logging]
    end
    
    CLI --> CLI_Handler
    API --> API_Handler
    CLI_Handler --> Business
    API_Handler --> Business
    Business --> BaseScraper
    BaseScraper --> LinkedInScraper
    BaseScraper --> NaukriScraper
    Business --> JobModel
    Business --> JobTagModel
    Business --> DTOs
    Business --> Utils
    BaseScraper --> Selenium
    BaseScraper --> RateLimiter
    Business --> MongoDB
    Business --> Logger
```

## Data Flow

### 1. Static Mode (Database Search)
```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI/API
    participant BL as Business Logic
    participant DB as MongoDB
    participant DTO as DTO Models
    
    U->>CLI: Request static search
    CLI->>BL: Process request
    BL->>DB: Query with filters
    DB-->>BL: Return job documents
    BL->>BL: Convert to Job objects
    BL->>DTO: Create response DTOs
    DTO-->>BL: Formatted response
    BL-->>CLI: Return results
    CLI-->>U: Display/return jobs
```

### 2. Dynamic Mode (Live Scraping)
```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI/API
    participant BL as Business Logic
    participant Scraper as Web Scraper
    participant Web as Target Website
    participant RL as Rate Limiter
    participant DB as MongoDB
    participant DTO as DTO Models
    
    U->>CLI: Request dynamic scraping
    CLI->>BL: Process request
    BL->>RL: Check rate limit
    RL-->>BL: Allow/deny
    BL->>Scraper: Initialize scraper
    Scraper->>Web: Navigate to page
    Web-->>Scraper: Return HTML
    Scraper->>Scraper: Parse job data
    Scraper->>Scraper: Add enhanced tags
    Scraper-->>BL: Return job objects
    BL->>DB: Save jobs (with deduplication)
    BL->>DTO: Create response DTOs
    DTO-->>BL: Formatted response
    BL-->>CLI: Return results
    CLI-->>U: Display/return jobs
```

## API Architecture

### REST API Design
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  CORS Middleware  │  Error Handling  │  Request Validation │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    API Endpoints                           │
├─────────────────────────────────────────────────────────────┤
│  GET /health     │  GET /jobs/search  │  GET /docs         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Response Models                          │
├─────────────────────────────────────────────────────────────┤
│  HealthResponse  │  JobSearchResponse  │  JobResponse      │
└─────────────────────────────────────────────────────────────┘
```

### API Request Flow
```mermaid
graph LR
    A[Client Request] --> B[CORS Check]
    B --> C[Request Validation]
    C --> D[Business Logic]
    D --> E[Database/Scraper]
    E --> F[Response Formatting]
    F --> G[Client Response]
    
    style A fill:#e1f5fe
    style G fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#f3e5f5
```

## Database Design

### MongoDB Collections

#### Jobs Collection
```json
{
  "_id": "ObjectId",
  "source": "linkedin|naukri",
  "mode": "static|dynamic",
  "title": "Software Engineer",
  "company": "Tech Corp",
  "location": "New York, NY",
  "salary": "$100,000",
  "salary_min": 100000,
  "salary_max": 150000,
  "currency": "USD",
  "tags": ["python", "django", "search:python"],
  "posted_date": "2024-01-01T00:00:00",
  "job_url": "https://linkedin.com/jobs/123",
  "is_remote": false,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

#### Job Tags Collection
```json
{
  "_id": "ObjectId",
  "name": "python",
  "count": 150,
  "category": "technology",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

### Database Indexes
```javascript
// Jobs Collection Indexes
db.jobs.createIndex({"source": 1, "job_url": 1}, {unique: true})
db.jobs.createIndex({"title": "text", "company": "text"})
db.jobs.createIndex({"posted_date": -1})
db.jobs.createIndex({"tags": 1})
db.jobs.createIndex({"is_remote": 1})

// Job Tags Collection Indexes
db.job_tags.createIndex({"name": 1}, {unique: true})
db.job_tags.createIndex({"category": 1})
```

## Scraping Engine

### Scraper Architecture
```mermaid
graph TB
    subgraph "Base Scraper (Abstract)"
        BS[BaseScraper]
        BS --> Init[Initialize WebDriver]
        BS --> Launch[Launch Browser]
        BS --> RateLimit[Apply Rate Limiting]
        BS --> AntiDetect[Anti-Detection Measures]
    end
    
    subgraph "Concrete Scrapers"
        LS[LinkedIn Scraper]
        NS[Naukri Scraper]
    end
    
    subgraph "Scraping Process"
        Navigate[Navigate to URL]
        Wait[Wait for Elements]
        Extract[Extract Job Data]
        Parse[Parse & Clean Data]
        Tag[Add Enhanced Tags]
        Yield[Yield Job Objects]
    end
    
    BS --> LS
    BS --> NS
    LS --> Navigate
    NS --> Navigate
    Navigate --> Wait
    Wait --> Extract
    Extract --> Parse
    Parse --> Tag
    Tag --> Yield
```

### Anti-Detection Strategy
```python
# Chrome Options for Anti-Detection
chrome_options = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--disable-javascript",  # Optional
    f"--user-agent={user_agent}"
]

# JavaScript Injection
driver.execute_script(
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
)
```

## Deployment Architecture

### Docker Compose Setup
```yaml
# Development Environment
services:
  job-scraper:
    build: .
    ports: ["8000:8000"]
    environment:
      - MONGODB_URI=mongodb://admin:password123@mongodb:27017/jobs_db
    depends_on: [mongodb]
    
  mongodb:
    image: mongo:7.0
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password123
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
    ports: ["27017:27017"]
    
  mongo-express:
    image: mongo-express:latest
    environment:
      - ME_CONFIG_MONGODB_ADMINUSERNAME=admin
      - ME_CONFIG_MONGODB_ADMINPASSWORD=password123
      - ME_CONFIG_MONGODB_URL=mongodb://admin:password123@mongodb:27017/
    ports: ["8081:8081"]
    depends_on: [mongodb]
```

### Production Architecture
```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end
    
    subgraph "Application Layer"
        API1[API Instance 1]
        API2[API Instance 2]
        API3[API Instance 3]
    end
    
    subgraph "Database Layer"
        MongoDB[(MongoDB Primary)]
        MongoDB_Replica[(MongoDB Replica)]
    end
    
    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana]
        Logs[ELK Stack]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    API1 --> MongoDB
    API2 --> MongoDB
    API3 --> MongoDB
    MongoDB --> MongoDB_Replica
    API1 --> Prometheus
    API2 --> Prometheus
    API3 --> Prometheus
    Prometheus --> Grafana
```

## Security & Rate Limiting

### Rate Limiting Strategy
```python
# Token Bucket Algorithm
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
```

### Security Measures
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: MongoDB parameterized queries
- **XSS Prevention**: Output sanitization
- **Rate Limiting**: Token bucket algorithm
- **CORS Configuration**: Controlled cross-origin requests
- **Error Handling**: No sensitive information in error messages

## Error Handling

### Error Handling Strategy
```mermaid
graph TD
    A[Request] --> B{Valid Request?}
    B -->|No| C[Return 400 Bad Request]
    B -->|Yes| D[Process Request]
    D --> E{Business Logic Success?}
    E -->|No| F[Log Error]
    F --> G[Return 500 Internal Server Error]
    E -->|Yes| H[Return Success Response]
    
    style C fill:#ffebee
    style G fill:#ffebee
    style H fill:#e8f5e8
```

### Error Categories
1. **Validation Errors** (400): Invalid input parameters
2. **Authentication Errors** (401): Unauthorized access
3. **Rate Limit Errors** (429): Too many requests
4. **Scraping Errors** (500): Website changes or network issues
5. **Database Errors** (500): Connection or query failures

## Performance Considerations

### Optimization Strategies

#### 1. Database Optimization
- **Indexing**: Strategic indexes for common queries
- **Connection Pooling**: Reuse database connections
- **Query Optimization**: Efficient MongoDB queries
- **Bulk Operations**: Batch insert/update operations

#### 2. Scraping Optimization
- **Headless Mode**: Faster browser execution
- **Resource Limiting**: Disable images, CSS, JavaScript
- **Parallel Scraping**: Multiple scrapers (with caution)
- **Caching**: Cache frequently accessed data

#### 3. API Optimization
- **Pagination**: Limit result sets
- **Response Caching**: Cache static responses
- **Async Processing**: Non-blocking operations
- **Compression**: Gzip response compression

### Performance Metrics
```python
# Key Performance Indicators
metrics = {
    "scraping_speed": "~1 job/second (with rate limiting)",
    "api_response_time": "< 100ms (cached)",
    "database_query_time": "< 50ms (indexed)",
    "concurrent_users": "100+ (with proper scaling)",
    "memory_usage": "~512MB per instance",
    "cpu_usage": "~20% under normal load"
}
```

## System Interactions

### Complete System Flow
```mermaid
graph TB
    subgraph "External Systems"
        LinkedIn[LinkedIn Jobs]
        Naukri[Naukri Jobs]
        Client[API Client]
    end
    
    subgraph "Application Layer"
        API[FastAPI Server]
        CLI[CLI Interface]
        Scrapers[Scraping Engine]
        DB[MongoDB Handler]
    end
    
    subgraph "Infrastructure"
        MongoDB[(MongoDB)]
        Redis[(Redis Cache)]
        Logs[Logging System]
    end
    
    Client --> API
    CLI --> Scrapers
    API --> Scrapers
    Scrapers --> LinkedIn
    Scrapers --> Naukri
    Scrapers --> DB
    API --> DB
    CLI --> DB
    DB --> MongoDB
    API --> Redis
    API --> Logs
    CLI --> Logs
    Scrapers --> Logs
    DB --> Logs
```

## Monitoring & Observability

### Health Checks
```python
# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_connected": db_handler.is_connected(),
        "scrapers_available": ["linkedin", "naukri"],
        "version": "1.0.0"
    }
```

### Logging Strategy
```python
# Structured Logging
logger.info("Jobs retrieved with filters", 
    filters=filter_dict,
    count=len(jobs),
    duration=scraping_time
)
```

### Metrics Collection
- **Request Count**: Total API requests
- **Response Time**: API response latency
- **Error Rate**: Failed requests percentage
- **Scraping Success Rate**: Successful scrapes
- **Database Performance**: Query execution time
- **Resource Usage**: CPU, memory, disk usage

---

## Architecture Benefits

1. **Scalability**: Horizontal scaling with Docker containers
2. **Maintainability**: Clear separation of concerns
3. **Testability**: Isolated components for unit testing
4. **Flexibility**: Easy to add new scrapers or data sources
5. **Reliability**: Comprehensive error handling and monitoring
6. **Performance**: Optimized for speed and resource usage
7. **Security**: Multiple layers of protection
8. **Observability**: Complete monitoring and logging

This architecture provides a robust foundation for a production-ready job scraping system that can handle high loads, maintain data quality, and scale efficiently.
