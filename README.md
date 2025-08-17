# Job Scraper

A job scraping application that extracts job listings from multiple sources including LinkedIn and Naukri. Built with Python, Selenium, and MongoDB.

## Features

- **Multi-Source Scraping**: LinkedIn and Naukri job listings with pagination support
- **Enhanced Tagging**: Automatic tag generation including search context, location, company, and salary information
- **MongoDB Integration**: Automatic saving of all scraped jobs with duplicate handling
- **Rate Limiting**: Respectful scraping with configurable limits and anti-bot detection
- **Dual Modes**: Static (database search) and Dynamic (live scraping) modes
- **Filtering**: Filter by query, company, location, source, and remote status
- **Pagination Support**: Pagination for large result sets
- **JSON Export**: Save results to JSON files with proper serialization
- **REST API**: FastAPI-based web API with endpoints
- **Command Line Interface**: CLI for all operations
- **Testing**: Unit and integration tests with fixtures
- **Structured Logging**: Detailed logging with structlog

## Requirements

### Option 1: Docker (Recommended)
- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

### Option 2: Local Installation
- Python 3.11+
- Chrome/Chromium browser
- MongoDB (optional, for database storage)
- Virtual environment

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd job-scraper
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up configuration:**
```bash
cp config.env.example .env
# Edit .env with your settings
```

5. **Install ChromeDriver (if not already installed):**
```bash
# macOS
brew install chromedriver

# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Or download from: https://chromedriver.chromium.org/
```

## Docker Setup (Recommended)

### Prerequisites
- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

### Quick Start with Docker

1. **Clone and navigate to the project:**
```bash
git clone <repository-url>
cd job-scraper
```

2. **Start all services:**
```bash
# Development mode
docker-compose up -d

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **Access services:**
- **Job Scraper API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB Express**: http://localhost:8081 (admin/password123)

### Docker Commands

#### Basic Operations
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### CLI Operations via Docker
```bash
# Static search from MongoDB
docker-compose exec job-scraper python main.py scrape-static --query "python" --limit 10

# Dynamic live scraping
docker-compose exec job-scraper python main.py scrape-dynamic --source linkedin --query "python" --limit 5

# Export jobs to JSON
docker-compose exec job-scraper python main.py export --output jobs.json

# Run tests
docker-compose exec job-scraper python -m pytest tests/ -v
```

#### API Operations via Docker
```bash
# Health check
curl http://localhost:8000/health

# Static search
curl "http://localhost:8000/jobs/search?query=python&mode=static&limit=5"

# Dynamic scraping
curl "http://localhost:8000/jobs/search?query=python&mode=dynamic&limit=5"

# Filtered search
curl "http://localhost:8000/jobs/search?query=python&company=Google&location=Bengaluru&source=linkedin&mode=static&limit=10"
```

#### Database Operations
```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh -u admin -p password123

# Backup database
docker-compose exec mongodb mongodump --out /backup

# View MongoDB Express
# Open http://localhost:8081 in browser (admin/password123)
```

#### Production Deployment
```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale job-scraper=3

# Monitor resources
docker stats

# View production logs
docker-compose logs -f job-scraper
```

#### Troubleshooting Docker
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs -f job-scraper

# Access container shell
docker-compose exec job-scraper bash

# Check Chrome/ChromeDriver in container
docker-compose exec job-scraper google-chrome --version
docker-compose exec job-scraper chromedriver --version

# Restart specific service
docker-compose restart job-scraper

# Clean up everything
docker-compose down -v
docker system prune -a
```

## Quick Start

> **Note**: Use Docker for the easiest setup and best experience. See [Docker Setup](#docker-setup-recommended) section above.

### Command Line Interface

```bash
# Static search from MongoDB database
python main.py scrape-static --query "python developer" --location "Bengaluru" --limit 10

# Dynamic live scraping from job sites
python main.py scrape-dynamic --source linkedin --query "python developer" --location "Bengaluru" --limit 10

# Export jobs to JSON file
python main.py export --query "software engineer" --location "Mumbai" --output jobs.json

# Start the API server
python main.py serve
```

### REST API

```bash
# Start the API server
python main.py serve

# The API will be available at:
# - API: http://localhost:8000
# - Interactive Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc

# Search for jobs via API (static mode)
curl "http://localhost:8000/jobs/search?query=python&location=Bengaluru&mode=static&limit=10"

# Live scraping via API (dynamic mode)
curl "http://localhost:8000/jobs/search?query=python&location=Bengaluru&mode=dynamic&limit=10"

# Health check
curl "http://localhost:8000/health"
```

### REST API

```bash
# Start the API server
python app.py

# The API will be available at:
# - API: http://localhost:8000
# - Interactive Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc

# Search for jobs via API
curl -X POST "http://localhost:8000/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "python developer", "location": "India", "limit": 10}'

# Filter jobs by company
curl -X POST "http://localhost:8000/jobs/filter" \
  -H "Content-Type: application/json" \
  -d '{"company": "Infosys", "is_remote": false}'
```

## 🔍 Enhanced Features

### Automatic Tagging System
The scraper automatically generates tags for each job:
- **Search Context**: `search:python`, `query:python developer`
- **Location Tags**: `location:Bengaluru`, `job_location:Bengaluru, Karnataka`
- **Company Tags**: `company:Infosys Limited`
- **Salary Tags**: `salary:₹8-15 LPA`
- **Source Tags**: `source:linkedin`, `source:naukri`
- **Mode Tags**: `mode:dynamic`, `mode:static`
- **Remote Tags**: `remote` (if applicable)

### MongoDB Integration
- **Automatic Saving**: All dynamic scraping results are automatically saved to MongoDB
- **Duplicate Handling**: Uses compound unique index on `(source, job_url)` to prevent duplicates
- **Pagination Support**: Pagination for large datasets in static mode
- **Filtering**: Filter by query, company, location, source, and remote status

### Dual Mode Operation
- **Static Mode**: Search existing jobs in MongoDB database
- **Dynamic Mode**: Live scraping from job sites with automatic MongoDB storage

### Usage Examples

```bash
# Static search with pagination
python main.py scrape-static --query "python" --location "Bengaluru" --limit 20 --offset 40

# Dynamic scraping with automatic MongoDB storage
python main.py scrape-dynamic --source naukri --query "software engineer" --location "Mumbai" --limit 50

# Export with filtering
python main.py export --query "data scientist" --company "Google" --location "Bangalore" --output data_jobs.json

# API with filtering
curl "http://localhost:8000/jobs/search?query=python&company=Infosys&location=Bengaluru&source=linkedin&mode=static&remote=false&limit=10&offset=0"
```

## 📖 Command Reference

### Static Search (MongoDB)
```bash
python main.py scrape-static [OPTIONS]

Options:
  --query TEXT     Job search query
  --company TEXT   Company name filter
  --location TEXT  Location filter
  --source TEXT    Source filter (linkedin, naukri)
  --remote BOOLEAN Remote work filter
  --limit INTEGER  Maximum number of jobs [default: 100, max: 1000]
  --offset INTEGER Number of jobs to skip for pagination [default: 0]
```

### Dynamic Scraping (Live)
```bash
python main.py scrape-dynamic [OPTIONS]

Options:
  --query TEXT     Job search query
  --company TEXT   Company name filter
  --location TEXT  Location filter
  --source TEXT    Source to scrape (linkedin, naukri) [default: linkedin]
  --remote BOOLEAN Remote work filter
  --limit INTEGER  Maximum number of jobs [default: 100, max: 1000]
```

### Export Jobs
```bash
python main.py export [OPTIONS]

Options:
  --query TEXT     Job search query
  --company TEXT   Company name filter
  --location TEXT  Location filter
  --source TEXT    Source filter (linkedin, naukri)
  --remote BOOLEAN Remote work filter
  --limit INTEGER  Maximum number of jobs [default: 100, max: 1000]
  --offset INTEGER Number of jobs to skip for pagination [default: 0]
  --output FILE    Output JSON file [default: jobs_YYYYMMDD_HHMMSS.json]
  --mode TEXT      Export mode (static, dynamic) [default: static]
```

### Start API Server
```bash
python main.py serve

# Starts FastAPI server on http://localhost:8000
# Interactive docs: http://localhost:8000/docs
```

### Docker Commands Reference

#### Container Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View running containers
docker-compose ps

# View logs
docker-compose logs -f
```

#### CLI via Docker
```bash
# All CLI commands work with docker-compose exec
docker-compose exec job-scraper python main.py [COMMAND] [OPTIONS]

# Examples:
docker-compose exec job-scraper python main.py scrape-static --query "python" --limit 10
docker-compose exec job-scraper python main.py scrape-dynamic --source linkedin --query "python" --limit 5
docker-compose exec job-scraper python main.py export --output jobs.json
docker-compose exec job-scraper python main.py serve
```

#### API via Docker
```bash
# API is automatically available at http://localhost:8000
curl http://localhost:8000/health
curl "http://localhost:8000/jobs/search?query=python&mode=dynamic&limit=5"
```

#### Database via Docker
```bash
# MongoDB is available at localhost:27017
# MongoDB Express UI: http://localhost:8081 (admin/password123)
docker-compose exec mongodb mongosh -u admin -p password123
```

## 🧪 Testing

### Run Unit Tests (Fast)
```bash
python run_tests.py unit
```

### Run Integration Tests (Slow)
```bash
python run_tests.py integration
```

### Run All Tests
```bash
python run_tests.py all
```

### Test Specific Components
```bash
# Test scrapers only
python run_tests.py scrapers

# Test database operations
python run_tests.py database
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `config.env.example`:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=jobs_db
JOBS_COLLECTION=jobs
TAGS_COLLECTION=job_tags

# Scraper Configuration
HEADLESS=true
REQUESTS_PER_SEC=1.0
TIMEZONE=Asia/Kolkata

# LinkedIn Configuration (optional)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Logging Configuration
LOG_LEVEL=INFO
```

### Settings

- `HEADLESS`: Run browser in headless mode (true/false)
- `REQUESTS_PER_SEC`: Rate limiting (requests per second)
- `TIMEZONE`: Timezone for date parsing
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Data Structure

### Job Object
```python
{
    "source": "linkedin",           # Source website
    "mode": "dynamic",              # Scraping mode
    "title": "Software Engineer",   # Job title
    "company": "Tech Corp",         # Company name
    "location": "New York, NY",     # Job location
    "salary": "$100,000",          # Salary (if available)
    "salary_min": 100000,          # Minimum salary
    "salary_max": 150000,          # Maximum salary
    "currency": "USD",             # Currency
    "tags": ["python", "django"],  # Job tags
    "posted_date": "2024-01-01",   # Posted date
    "job_url": "https://...",      # Job URL
    "is_remote": false             # Remote work flag
}
```

## Database Schema

### Jobs Collection
- `_id`: MongoDB ObjectId
- `source`: Source website
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `salary`: Salary information
- `tags`: Array of job tags
- `posted_date`: Posted date
- `job_url`: Job URL (unique)
- `is_remote`: Remote work flag
- `created_at`: Record creation timestamp

### Tags Collection
- `tag`: Tag name (unique)
- `count`: Usage count
- `category`: Tag category
- `created_at`: Tag creation timestamp
- `updated_at`: Last update timestamp

## Development

### Project Structure
```
job-scraper/
├── main.py                 # CLI application
├── app.py                  # FastAPI REST API
├── scrapers/              # Scraper modules
│   ├── base_scraper.py    # Base scraper class
│   ├── linkedin_scraper.py # LinkedIn scraper
│   └── naukri_scraper.py  # Naukri scraper
├── da/                    # Data access layer
│   ├── dao.py            # Data models
│   └── database.py       # Database operations
├── utils/                 # Utilities
│   ├── logger.py         # Logging configuration
│   └── utils.py          # Helper functions
├── configs/              # Configuration
│   └── settings.py       # Application settings
├── rate_limiter/         # Rate limiting
│   └── rate_limit.py     # Token bucket implementation
├── tests/                # Test suite
│   ├── conftest.py       # Test configuration
│   └── test_*.py         # Test files
├── dto/                  # Data Transfer Objects
│   └── models.py         # API response models
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── docker-compose.prod.yml # Production Docker setup
├── mongo-init.js         # MongoDB initialization
└── requirements.txt      # Dependencies
```

### Adding New Scrapers

1. Create a new scraper class inheriting from `BaseScraper`
2. Implement the `scrape()` method
3. Add the scraper to the main application
4. Write unit and integration tests

Example:
```python
from scrapers.base_scraper import BaseScraper

class NewScraper(BaseScraper):
    def scrape(self, query: str, location: str | None, limit: int):
        # Implementation here
        pass
```

## 🚨 Important Notes

### Rate Limiting
- The application includes rate limiting to be respectful to websites
- Default: 1 request per second
- Adjust `REQUESTS_PER_SEC` in settings if needed

### Legal Considerations
- Always review and comply with website Terms of Service
- Use scraped data responsibly
- Consider implementing delays between requests
- Some websites may block automated access

### Anti-Detection
- The application uses headless Chrome with realistic user agents
- Consider using proxies for production use
- Implement additional anti-detection measures as needed

## 🐛 Troubleshooting

### ChromeDriver Issues
```bash
# Check ChromeDriver version
chromedriver --version

# Remove quarantine attribute (macOS)
xattr -d com.apple.quarantine $(which chromedriver)
```

### Docker Issues
```bash
# Check if containers are running
docker-compose ps

# View container logs
docker-compose logs -f job-scraper

# Check Chrome/ChromeDriver in container
docker-compose exec job-scraper google-chrome --version
docker-compose exec job-scraper chromedriver --version

# Restart specific service
docker-compose restart job-scraper

# Rebuild container
docker-compose build --no-cache job-scraper

# Access container shell for debugging
docker-compose exec job-scraper bash

# Check container health
docker-compose exec job-scraper curl -f http://localhost:8000/health
```

### Database Connection Issues
- Ensure MongoDB is running
- Check connection string in `.env`
- Verify network connectivity

### Scraping Issues
- Check internet connection
- Verify website accessibility
- Review rate limiting settings
- Check for website changes

## 📈 Performance

### Benchmarks
- **Unit Tests**: < 1 second
- **Integration Tests**: 5-60 seconds per test
- **Scraping Speed**: ~1 job per second (with rate limiting)
- **Database Operations**: < 100ms per operation

### Optimization Tips
- Use headless mode for faster execution
- Implement caching for repeated queries
- Use bulk database operations
- Consider parallel scraping (with caution)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. Users are responsible for complying with website Terms of Service and applicable laws. The authors are not responsible for any misuse of this software.
