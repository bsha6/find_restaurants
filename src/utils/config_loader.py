"""
Configuration loading utilities for the restaurant finder project.

This module handles loading configuration data from various file formats,
with a focus on markdown-based URL management for web scraping operations.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def load_urls_from_markdown(file_path: str = "src/config/urls_to_scrape.md") -> List[str]:
    """
    Load URLs from a markdown file.
    
    Args:
        file_path (str): Path to the markdown file containing URLs.
        
    Returns:
        List[str]: List of URLs found in the markdown file.
    """
    urls = []
    
    # Get the absolute path relative to the project root
    if not os.path.isabs(file_path):
        # Get the project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        file_path = str(project_root / file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract URLs using regex - look for http/https URLs
        url_pattern = r'https?://[^\s\)]+(?:[^\s\.\)\,])'
        found_urls = re.findall(url_pattern, content)
        
        # Clean up URLs and filter for Eater domains
        for url in found_urls:
            url = url.strip()
            if 'eater.com' in url:
                urls.append(url)
                
        logger.info(f"Loaded {len(urls)} URLs from {file_path}")
        return urls
        
    except FileNotFoundError:
        logger.error(f"URL config file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading URLs from {file_path}: {e}")
        return []


def load_urls_by_region_from_markdown(file_path: str = "src/config/urls_to_scrape.md") -> Dict[str, List[str]]:
    """
    Load URLs from a markdown file organized by region/city.
    
    Args:
        file_path (str): Path to the markdown file containing URLs.
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping region names to lists of URLs.
    """
    regions = {}
    current_region = None
    
    # Get the absolute path relative to the project root
    if not os.path.isabs(file_path):
        project_root = Path(__file__).parent.parent.parent
        file_path = str(project_root / file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            
            # Check for region headers (## Region Name)
            if line.startswith('## ') and not line.startswith('## Notes'):
                current_region = line[3:].strip()  # Remove "## " prefix
                regions[current_region] = []
                continue
                
            # Extract URLs from list items
            if line.startswith('- https') and current_region:
                url_match = re.search(r'https?://[^\s\)]+(?:[^\s\.\)\,])', line)
                if url_match and 'eater.com' in url_match.group():
                    regions[current_region].append(url_match.group())
                    
        logger.info(f"Loaded URLs for {len(regions)} regions from {file_path}")
        return regions
        
    except FileNotFoundError:
        logger.error(f"URL config file not found: {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading URLs by region from {file_path}: {e}")
        return {}


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: Path to the project root directory.
    """
    return Path(__file__).parent.parent.parent


def load_config_file(file_path: str, relative_to_project: bool = True) -> Optional[str]:
    """
    Load content from a configuration file.
    
    Args:
        file_path (str): Path to the configuration file.
        relative_to_project (bool): Whether the path is relative to project root.
        
    Returns:
        Optional[str]: File content or None if file not found.
    """
    if relative_to_project and not os.path.isabs(file_path):
        file_path = str(get_project_root() / file_path)
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading config file {file_path}: {e}")
        return None 