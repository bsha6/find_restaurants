# Where to Eat

A Python project for scraping, processing, and enriching restaurant data from food blogs and guides. Features concurrent web scraping, LLM-powered data enrichment, and export capabilities for mapping applications.

## Prerequisites

- Python 3.13.4 or higher
- [direnv](https://direnv.net/) for environment management
- [Conda](https://docs.conda.io/en/latest/) for package management

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd find_restaurants
```

2. Install direnv:
```bash
# On macOS with Homebrew
brew install direnv

# On Linux
sudo apt-get install direnv  # Ubuntu/Debian
# or
sudo dnf install direnv      # Fedora
```

3. Add direnv hook to your shell:
```bash
# Add to ~/.bashrc or ~/.zshrc
eval "$(direnv hook bash)"  # for bash
# or
eval "$(direnv hook zsh)"   # for zsh
```

4. Allow direnv in the project directory:
```bash
direnv allow
```

5. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate find_food
```

## Project Structure

```
src/
├── main.py                    # CLI entry point with commands
├── database/                  # Database management
│   ├── models.py             # SQLAlchemy models
│   ├── crud.py               # Database operations
│   ├── database.py           # Database connection
│   └── init_db.py            # Database initialization
├── scrape/                    # Web scraping modules
│   └── eater_blog.py         # Eater.com scraper with concurrent support
├── utils/                     # Utility functions
│   └── output_data.py        # Data export utilities
└── resources/                 # Data storage and resources
    └── eater/                # Scraped data from Eater.com
tests/
├── unit/                     # Unit tests
│   ├── conftest.py          # Test fixtures and configuration
│   ├── test_cli.py          # CLI testing
│   ├── test_database.py     # Database testing
│   └── test_eater_blog.py   # Scraper testing
logs/                         # Application logs
prompts/                      # LLM prompts for data enrichment
```

## Usage

### Basic Commands

Initialize the database:
```bash
python -m src.main init
```

Check system status:
```bash
python -m src.main status
```

Scrape restaurant data from Eater blogs:
```bash
# Scrape using default configured URLs
python -m src.main scrape

# Scrape specific URLs
python -m src.main scrape https://dc.eater.com/maps/dc-best-restaurants-38

# Concurrent scraping with custom workers
python -m src.main scrape url1 url2 url3 --workers 5
```

List restaurants in the database:
```bash
# Show recent restaurants
python -m src.main list

# Search by name
python -m src.main list --search "pizza"

# Filter by source
python -m src.main list --source "eater.com"
```

Export data:
```bash
# Export to TSV (default)
python -m src.main export

# Export to CSV with custom filename
python -m src.main export --format csv --output my_restaurants.csv

# Include LLM-generated fields
python -m src.main export --include-llm
```

### Configuration

View current configuration:
```bash
python -m src.main config show
```

Set configuration values:
```bash
# Set default URLs for scraping
python -m src.main config set default_urls "url1,url2,url3"

# Set number of workers for concurrent scraping
python -m src.main config set max_workers 10

# Set rate limiting delay
python -m src.main config set rate_limit_delay 2.0
```

Reset configuration to defaults:
```bash
python -m src.main config reset
```

## Features

### Data Collection
- **Multi-source scraping**: Currently supports Eater.com with extensible architecture
- **Concurrent processing**: Configurable worker threads for faster data collection
- **Rate limiting**: Respectful crawling with configurable delays
- **Error handling**: Robust error recovery and logging

### Data Enrichment
- **LLM-powered analysis**: Automatic extraction of cuisine type, atmosphere, and notable features
- **Standardized schema**: Consistent data structure across all sources
- **Quality validation**: Confidence scoring and manual review capabilities

### Data Management
- **SQLite database**: Efficient local storage with full CRUD operations
- **Export formats**: TSV and CSV export for Google My Maps and other applications
- **Search and filtering**: Find restaurants by name, cuisine, or source
- **Configuration system**: Persistent settings with easy management

### Core Data Schema
- Restaurant name, address, and description
- Source tracking with URLs and timestamps
- LLM-enriched fields: cuisine type, vibe/atmosphere, price point
- Notable dishes and special features
- Local popularity and reputation indicators

## Development

To run tests:
```bash
pytest
```

## Current Status & Roadmap

### ✅ Completed Features
- [X] SQLite database with proper schema and migrations
- [X] Concurrent web scraping with configurable workers
- [X] LLM-powered data enrichment (cuisine, vibe, etc.)
- [X] Comprehensive CLI with multiple commands
- [X] Configuration management system
- [X] Data export to multiple formats (TSV, CSV)
- [X] Error handling and logging infrastructure
- [X] Unit test framework with fixtures
- [X] Rate limiting and respectful crawling

### 🚧 In Progress
- [ ] [Google Maps API integration](https://github.com/bsha6/find_restaurants/issues/1) for reviews and hours

### 📋 Future Enhancements
- [ ] Additional data sources beyond Eater.com
- [ ] Integration test coverage
- [ ] Performance optimizations for large datasets
- [ ] Data science experiments to discover similar restaurants

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
