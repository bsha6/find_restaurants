# Restaurant Data Collection and Processing System

## Project Overview
This project aims to create a comprehensive database of restaurants from various sources, with a focus on high-quality food establishments. The data will be processed and enriched using LLMs to provide additional insights, ultimately creating a format suitable for Google My Maps integration.

## Data Sources
- Eater.com (initial source)
- Future sources to be added (e.g., Michelin Guide, local food blogs, etc.)

## Data Schema
### Core Restaurant Information
- Name
- Address
- Description
- Source
- Source URL
- Last Updated

### LLM-Enriched Fields
- Cuisine
- Vibe/Atmosphere
- Notable Dishes
- Special Features (outdoor seating, reservations required, etc.)
- Price Point (budget, mid-range, high-end)
- Local Popularity/Reputation

## Technical Components

### 1. Data Collection
- Web scraper for Eater.com
  - Focus on restaurant listings
  - Extract core information
  - Handle pagination and regional sections
- Extensible architecture for adding new sources
- Rate limiting and respectful crawling practices

### 2. Data Storage
- SQLite database for local storage
- Schema versioning
- Data validation and cleaning

- Duplicate detection and merging

### 3. LLM Processing Pipeline
- Text extraction from source content
- Prompt engineering for consistent field extraction
- Batch processing for efficiency
- Confidence scoring for LLM outputs
- Manual review interface for low-confidence results

### 4. Export System
- TSV generation for Google My Maps
- Custom field mapping
- Data validation before export
- Backup and versioning

## Future Enhancements
1. User Interface
   - Web interface for data management
   - Manual entry and editing
   - Review and approval workflow

2. Additional Data Sources
   - Integration with review platforms
   - Social media sentiment analysis
   - Local food blogs and guides

3. Advanced Features
   - Recommendation system
   - Seasonal menu tracking
   - Price history tracking
   - Special events and pop-ups

## Development Phases

### Phase 1: Foundation
- Set up project structure
- Implement basic Eater.com scraper
- Create SQLite database schema
- Develop basic LLM processing pipeline

### Phase 2: Enhancement
- Implement advanced data cleaning
- Add more data sources
- Improve LLM prompts and processing
- Create export system

### Phase 3: Exploratory
- Use Google Maps APIs to extract additional features? Customer reviews?

## Success Metrics
- Number of restaurants in database
- Data completeness
- LLM processing accuracy
- Export success rate
- System performance

## Notes for LLMs
- Focus on maintaining data quality and consistency
- Consider cultural context in cuisine classification
- Account for regional variations in restaurant types
- Handle multilingual content appropriately
- Consider seasonal variations in restaurant data

## Improvements
- Scalability & Performance
  - Single-threaded Scraping: Right now, you're scraping URLs one at a time. That's fine for a couple of URLs, but if you want to scale, you need to go async or multi-threaded. Otherwise, you'll be waiting all day for your data.
  - Database Connections: You're calling next(get_db()) inside the loop. If get_db() is a generator that yields a session, you might want to manage your session context better, especially if you go multi-threaded.
- Error Handling
  - Broad Exception Catching: You're catching Exception everywhere. That's like using a bazooka to kill a fly. Be more specific where you can, so you don't hide real bugs.
  - Logging Sensitive Data: You're logging response headers and saving HTML to a file. That's cool for debugging, but don't do that in production unless you want to fill up your disk and maybe leak some sensitive info.
- Code Quality & Best Practices
  - Magic Strings: You've got class names like 'hkfm3hg' and 'duet--article--map-card' hardcoded. If Eater changes their markup, your code breaks. Consider making these constants at the top of your file, or better yet, make them configurable.
  - Function Length: extract_restaurant_data is getting a little chunky. Break it up if you can—maybe one function for parsing JSON-LD, another for extracting from the map card.
  - Type Hints: You're using them in some places, but not everywhere. Be consistent. It helps with readability and tooling.
  - Testing: I don't see any tests here. You better have some in tests/ or I'm gonna be real mad. If you don't, write some. Use fixtures and mocks for your DB and HTTP calls.
- Extensibility
  - Hardcoded Source Extraction: You're using tldextract to get the domain, but you're assuming the source is always the domain of the restaurant URL. That might not always be true. Make it flexible.
  - No Rate Limiting: If you start scraping a lot, you might get blocked. Consider adding a delay or using a pool of proxies.
- Other Nits
  - Unused Imports: Double-check if you're using everything you import.
  - Docstrings: Good start, but make sure they're up to date and clear.
  - Main Guard: You've got a __main__ block, but you're running real scrapes there. For production, make a CLI or a proper entrypoint.
- Scalability Suggestions
  - Parallelization: Use concurrent.futures.ThreadPoolExecutor or asyncio with aiohttp for fetching multiple URLs at once.
  - Queue System: For serious scale, use a task queue like Celery or RQ. That way, you can distribute scraping jobs.
  - Configurable Settings: Move magic strings and constants to a config file or environment variables.
  - Monitoring: Add metrics (Prometheus, Sentry, whatever) so you know when things go wrong at scale.
  - Testing: Mock your HTTP requests and DB calls. Use pytest fixtures, and check your conftest.py for reusable mocks.
