#!/usr/bin/env python3
"""
Restaurant Data Collection CLI

A command-line interface for scraping, processing, and exporting restaurant data.
"""

import click
import logging
import sys
from pathlib import Path
from typing import List
import json
import time
from datetime import datetime

from src.scrape.eater_blog import scrape_eater_blog, scrape_eater_blogs_concurrently
from src.database.database import get_db
from src.database.init_db import init_db
from src.database import crud
from src.utils.output_data import save_to_tsv


# Configure logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)  # Create log directory if it doesn't exist

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / 'restaurant_cli.log')
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration management for the CLI."""
    
    def __init__(self):
        self.config_file = Path.home() / '.restaurant_scraper_config.json'
        self.default_config = {
            'max_workers': 5,
            'rate_limit_delay': 1.0,
            'output_directory': 'src/resources/eater',
            'default_urls': [
                'https://dc.eater.com/maps/dc-best-restaurants-38',
                'https://www.eater.com/maps/best-new-restaurants-columbus-ohio'
            ],
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                return {**self.default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value


# Global config instance
config = Config()


def setup_database():
    """Initialize the database if needed."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def progress_callback(current: int, total: int, item: str = ""):
    """Progress reporting callback."""
    percentage = (current / total) * 100 if total > 0 else 0
    bar_length = 50
    filled_length = int(bar_length * current // total) if total > 0 else 0
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    click.echo(f'\r|{bar}| {percentage:.1f}% ({current}/{total}) {item}', nl=False)
    if current == total:
        click.echo()  # New line when complete


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config-file', help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config_file):
    """Restaurant Data Collection CLI - Scrape, process, and export restaurant data."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if config_file:
        config.config_file = Path(config_file)
        config.config = config.load_config()
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.argument('urls', nargs=-1, required=False)
@click.option('--workers', '-w', default=None, type=int, help='Number of concurrent workers')
@click.option('--delay', '-d', default=None, type=float, help='Delay between requests (seconds)')
@click.option('--save-html', is_flag=True, help='Save HTML responses for debugging')
@click.pass_context
def scrape(ctx, urls, workers, delay, save_html):
    """Scrape restaurant data from Eater blog URLs.
    
    URLs can be provided as arguments. If none provided, uses configured default URLs.
    
    Examples:
        python -m src.main scrape
        python -m src.main scrape https://dc.eater.com/maps/dc-best-restaurants-38
        python -m src.main scrape url1 url2 url3 --workers 3
    """
    cfg = ctx.obj['config']
    
    # Use provided URLs or fall back to configured defaults
    if not urls:
        urls = cfg.get('default_urls', [])
        if not urls:
            click.echo("❌ No URLs provided and no default URLs configured.", err=True)
            click.echo("Use 'config set default_urls URL1,URL2' to set defaults or provide URLs as arguments.")
            sys.exit(1)
    
    # Override config with command-line options
    workers = workers or cfg.get('max_workers', 5)
    delay = delay or cfg.get('rate_limit_delay', 1.0)
    
    click.echo("🍴 Starting restaurant scraping operation")
    click.echo(f"📋 URLs to scrape: {len(urls)}")
    click.echo(f"⚡ Workers: {workers}")
    click.echo(f"⏱️  Delay between requests: {delay}s")
    
    if save_html:
        click.echo("🐛 HTML debugging enabled - responses will be saved")
    
    # Ensure database is ready
    setup_database()
    
    start_time = time.time()
    
    try:
        if len(urls) == 1:
            # Single URL - provide detailed progress
            url = urls[0]
            click.echo(f"\n🔍 Scraping: {url}")
            restaurants = scrape_eater_blog(url)
            click.echo(f"✅ Successfully scraped {len(restaurants)} restaurants")
        else:
            # Multiple URLs - use concurrent scraping
            click.echo(f"\n🚀 Starting concurrent scraping of {len(urls)} URLs...")
            scrape_eater_blogs_concurrently(list(urls), max_workers=workers)
            click.echo("✅ Concurrent scraping completed")
        
        elapsed = time.time() - start_time
        click.echo(f"\n🎉 Scraping operation completed in {elapsed:.2f} seconds")
        
        # Show summary from database
        with get_db() as db:
            total_restaurants = len(crud.get_restaurants(db, limit=10000))
            click.echo(f"📊 Total restaurants in database: {total_restaurants}")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        click.echo(f"❌ Scraping failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', default='tsv', type=click.Choice(['tsv', 'csv', 'json']), help='Export format')
@click.option('--output', '-o', help='Output filename (auto-generated if not provided)')
@click.option('--limit', '-l', type=int, help='Limit number of restaurants to export')
@click.option('--include-llm', is_flag=True, help='Include LLM-generated fields in export')
@click.pass_context
def export(ctx, format, output, limit, include_llm):
    """Export restaurant data to various formats.
    
    Examples:
        python -m src.main export
        python -m src.main export --format csv --output my_restaurants.csv
        python -m src.main export --limit 100 --include-llm
    """
    cfg = ctx.obj['config']
    
    click.echo("📤 Starting export operation")
    
    try:
        with get_db() as db:
            # Use configured limit if none provided
            export_limit = limit or 10000
            restaurants = crud.get_restaurants(db, limit=export_limit)
            
            if not restaurants:
                click.echo("❌ No restaurants found in database. Run scraping first.", err=True)
                sys.exit(1)
            
            click.echo(f"📊 Found {len(restaurants)} restaurants to export")
            
            # Convert to dictionaries for export
            restaurant_data = []
            for r in restaurants:
                data = {
                    'name': r.name,
                    'address': r.address,
                    'description': r.description,
                    'source': r.source,
                    'source_url': r.source_url,
                    'created_at': r.created_at.isoformat() if r.created_at is not None else None,
                    'updated_at': r.updated_at.isoformat() if r.updated_at is not None else None
                }
                
                # Add LLM fields if requested and available
                if include_llm and r.llm_info:
                    llm_data = {
                        'cuisine': r.llm_info.cuisine,
                        'vibe_atmosphere': r.llm_info.vibe,  # Note: model uses 'vibe' not 'vibe_atmosphere'
                        'llm_model_version': r.llm_info.llm_model_version,
                        'generated_at': r.llm_info.generated_at.isoformat() if r.llm_info.generated_at is not None else None
                    }
                    data.update(llm_data)
                
                restaurant_data.append(data)
            
            # Determine output path using configuration
            if not output:
                # Use configured output directory
                output_dir = Path(cfg.get('output_directory', '.'))
                output_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                llm_suffix = '_with_llm' if include_llm else ''
                filename = f"restaurants_{timestamp}{llm_suffix}.{format}"
                output = output_dir / filename
            else:
                # Ensure output path is a Path object and create parent directories
                output = Path(output)
                output.parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if format == 'tsv':
                save_to_tsv(restaurant_data, str(output))
                click.echo(f"💾 Saved {len(restaurant_data)} restaurants to {output}")
            elif format == 'csv':
                import pandas as pd
                df = pd.DataFrame(restaurant_data)
                df.to_csv(output, index=False)
                click.echo(f"💾 Saved {len(restaurant_data)} restaurants to {output}")
            elif format == 'json':
                with open(output, 'w') as f:
                    json.dump(restaurant_data, f, indent=2, default=str)
                click.echo(f"💾 Saved {len(restaurant_data)} restaurants to {output}")
            
            click.echo(f"✅ Export completed: {len(restaurant_data)} restaurants exported to {output}")
            
            # Log the export operation
            logger.info(f"Exported {len(restaurant_data)} restaurants to {output} in {format} format")
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=10, help='Number of restaurants to show')
@click.option('--search', '-s', help='Search by restaurant name')
@click.option('--source', help='Filter by source domain')
def list(limit, search, source):
    """List restaurants in the database.
    
    Examples:
        python -m src.main list
        python -m src.main list --limit 20
        python -m src.main list --search "pizza"
        python -m src.main list --source eater
    """
    click.echo("📋 Listing restaurants from database")
    
    try:
        with get_db() as db:
            # Get restaurants with basic filtering
            restaurants = crud.get_restaurants(db, limit=limit)
            
            if search:
                restaurants = [r for r in restaurants if search.lower() in (r.name or "").lower()]
            
            if source:
                restaurants = [r for r in restaurants if source.lower() in (r.source or "").lower()]
            
            if not restaurants:
                click.echo("❌ No restaurants found matching criteria.")
                return
            
            click.echo(f"\n🍴 Found {len(restaurants)} restaurants:")
            click.echo("-" * 80)
            
            for i, r in enumerate(restaurants, 1):
                click.echo(f"{i:2d}. {r.name}")
                click.echo(f"    📍 {r.address}")
                click.echo(f"    🌐 {r.source}")
                if r.description is not None and len(str(r.description)) > 0:
                    desc_str = str(r.description)
                    desc = desc_str[:100] + "..." if len(desc_str) > 100 else desc_str
                    click.echo(f"    📝 {desc}")
                click.echo()
            
    except Exception as e:
        logger.error(f"List operation failed: {e}")
        click.echo(f"❌ List operation failed: {e}", err=True)
        sys.exit(1)


@cli.group()
def config_cmd():
    """Configuration management commands."""
    pass


@config_cmd.command('show')
def config_show():
    """Show current configuration."""
    click.echo("🔧 Current Configuration:")
    click.echo("-" * 40)
    for key, value in config.config.items():
        if isinstance(value, List):
            click.echo(f"{key}:")
            for item in value:
                click.echo(f"  - {item}")
        else:
            click.echo(f"{key}: {value}")


@config_cmd.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value.
    
    For lists (like default_urls), use comma-separated values.
    
    Examples:
        python -m src.main config set max_workers 10
        python -m src.main config set default_urls "url1,url2,url3"
    """
    # Handle special cases for different value types
    if key == 'max_workers':
        value = int(value)
    elif key == 'rate_limit_delay':
        value = float(value)
    elif key == 'default_urls':
        value = [url.strip() for url in value.split(',')]
    
    config.set(key, value)
    config.save_config()
    click.echo(f"✅ Set {key} = {value}")


@config_cmd.command('reset')
@click.confirmation_option(prompt='Are you sure you want to reset all configuration to defaults?')
def config_reset():
    """Reset configuration to defaults."""
    config.config = config.default_config.copy()
    config.save_config()
    click.echo("✅ Configuration reset to defaults")


@cli.command()
def init():
    """Initialize the database and configuration."""
    click.echo("🚀 Initializing Restaurant Scraper...")
    
    try:
        # Initialize database
        setup_database()
        click.echo("✅ Database initialized")
        
        # Save default configuration
        config.save_config()
        click.echo(f"✅ Configuration saved to {config.config_file}")
        
        click.echo("\n🎉 Initialization complete!")
        click.echo("\nNext steps:")
        click.echo("  1. Run 'python -m src.main scrape' to start scraping")
        click.echo("  2. Run 'python -m src.main list' to view collected data")
        click.echo("  3. Run 'python -m src.main export' to export data")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        click.echo(f"❌ Initialization failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Show system status and statistics."""
    click.echo("📊 Restaurant Scraper Status")
    click.echo("=" * 40)
    
    try:
        with get_db() as db:
            total_restaurants = len(crud.get_restaurants(db, limit=10000))
            click.echo(f"🍴 Total restaurants: {total_restaurants}")
            
            # Get source breakdown
            restaurants = crud.get_restaurants(db, limit=10000)
            sources = {}
            for r in restaurants:
                sources[r.source] = sources.get(r.source, 0) + 1
            
            if sources:
                click.echo("\n📈 Breakdown by source:")
                for source, count in sources.items():
                    click.echo(f"  {source}: {count}")
            
            # Recent activity - simplified to avoid SQLAlchemy Column sorting issues
            if restaurants:
                click.echo(f"\n🕒 Most recent restaurant: {restaurants[0].name}")
        
        # Configuration info
        click.echo(f"\n⚙️  Configuration file: {config.config_file}")
        click.echo(f"🔧 Max workers: {config.get('max_workers')}")
        click.echo(f"⏱️  Rate limit delay: {config.get('rate_limit_delay')}s")
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        click.echo(f"❌ Status check failed: {e}", err=True)


# Add the config command group to the main CLI
cli.add_command(config_cmd, name='config')


def main():
    """Entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
