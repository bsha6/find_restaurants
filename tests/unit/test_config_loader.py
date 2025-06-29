import pytest
from unittest.mock import patch, mock_open, Mock
from pathlib import Path
import os
import tempfile

from src.utils.config_loader import (
    load_urls_from_markdown,
    load_urls_by_region_from_markdown,
    get_project_root,
    load_config_file
)


@pytest.fixture
def sample_markdown_content():
    """Provide sample markdown content with URLs for testing."""
    return """# Eater Blog URLs to Scrape (organized by City)

## Washington DC
- https://dc.eater.com/maps/dc-best-restaurants-38
- https://dc.eater.com/maps/best-new-restaurants-heatmap-dc

## Columbus, Ohio
- https://www.eater.com/maps/best-new-restaurants-columbus-ohio

## SF
- https://sf.eater.com/maps/best-restaurants-san-francisco-38
- https://sf.eater.com/maps/best-new-restaurants-san-francisco

## NYC
- https://ny.eater.com/maps/best-new-york-restaurants-38-map
- https://ny.eater.com/maps/best-new-nyc-restaurants-heatmap

## Notes
- URLs are organized by city/region for easy management
- Add new URLs under the appropriate city heading
"""


@pytest.fixture
def mixed_urls_markdown():
    """Provide markdown content with mixed (Eater and non-Eater) URLs."""
    return """# Mixed URLs

## Test Section
- https://dc.eater.com/maps/valid-eater-url
- https://example.com/not-an-eater-url
- https://sf.eater.com/maps/another-valid-url
- https://yelp.com/should-be-ignored
"""


@pytest.fixture
def empty_markdown():
    """Provide empty markdown content."""
    return """# Empty File

No URLs here!
"""


@pytest.fixture
def malformed_markdown():
    """Provide markdown with malformed URLs."""
    return """# Bad URLs

## Test
- not-a-url-at-all
- https://
- https://eater.
"""


# Happy Path Tests

def test_load_urls_from_markdown_success(sample_markdown_content):
    """Test successful loading of URLs from markdown content."""
    mock_file = mock_open(read_data=sample_markdown_content)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):  # Mock absolute path
            result = load_urls_from_markdown("/absolute/path/to/file.md")
    
    assert len(result) == 7
    assert "https://dc.eater.com/maps/dc-best-restaurants-38" in result
    assert "https://sf.eater.com/maps/best-restaurants-san-francisco-38" in result
    assert "https://ny.eater.com/maps/best-new-york-restaurants-38-map" in result


def test_load_urls_from_markdown_filters_eater_only(mixed_urls_markdown):
    """Test that only Eater URLs are returned, filtering out other domains."""
    mock_file = mock_open(read_data=mixed_urls_markdown)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):
            result = load_urls_from_markdown("/test/path")
    
    assert len(result) == 2
    assert "https://dc.eater.com/maps/valid-eater-url" in result
    assert "https://sf.eater.com/maps/another-valid-url" in result
    assert "https://example.com/not-an-eater-url" not in result
    assert "https://yelp.com/should-be-ignored" not in result


def test_load_urls_from_markdown_relative_path():
    """Test path resolution for relative paths."""
    mock_file = mock_open(read_data="- https://test.eater.com/url")
    
    with patch("builtins.open", mock_file):
        with patch("src.utils.config_loader.get_project_root", return_value=Path("/mocked/root")):
            result = load_urls_from_markdown("relative/path/file.md")
    
    assert len(result) == 1
    assert "https://test.eater.com/url" in result


# Edge Cases and Error Handling

def test_load_urls_from_markdown_file_not_found():
    """Test handling when markdown file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_urls_from_markdown("/nonexistent/file.md")
    
    assert result == []


def test_load_urls_from_markdown_empty_file(empty_markdown):
    """Test handling of empty markdown file."""
    mock_file = mock_open(read_data=empty_markdown)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):
            result = load_urls_from_markdown("/test/empty.md")
    
    assert result == []


def test_load_urls_from_markdown_no_eater_urls():
    """Test handling when no Eater URLs are found."""
    content = """# Non-Eater URLs
- https://example.com/url1
- https://yelp.com/url2
"""
    mock_file = mock_open(read_data=content)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):
            result = load_urls_from_markdown("/test/file.md")
    
    assert result == []


def test_load_urls_from_markdown_permission_error():
    """Test handling of file permission errors."""
    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        result = load_urls_from_markdown("/restricted/file.md")
    
    assert result == []


def test_load_urls_from_markdown_malformed_content(malformed_markdown):
    """Test handling of markdown with malformed URLs."""
    mock_file = mock_open(read_data=malformed_markdown)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):
            result = load_urls_from_markdown("/test/malformed.md")
    
    # Should handle malformed URLs gracefully
    assert result == []


# Regional Loading Tests

def test_load_urls_by_region_success(sample_markdown_content):
    """Test successful loading of URLs organized by region."""
    mock_file = mock_open(read_data=sample_markdown_content)
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=True):
            result = load_urls_by_region_from_markdown("/test/file.md")
    
    assert len(result) == 4  # DC, Columbus Ohio, SF, NYC
    assert "Washington DC" in result
    assert "SF" in result
    assert "NYC" in result
    assert "Columbus, Ohio" in result
    
    # Check specific region content
    assert len(result["Washington DC"]) == 2
    assert len(result["SF"]) == 2
    assert "https://dc.eater.com/maps/dc-best-restaurants-38" in result["Washington DC"]


def test_load_urls_by_region_file_not_found():
    """Test regional loading when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_urls_by_region_from_markdown("/nonexistent/file.md")
    
    assert result == {}


# Utility Function Tests

def test_get_project_root():
    """Test project root path calculation."""
    result = get_project_root()
    
    # Should be a Path object pointing 3 levels up from config_loader.py
    assert isinstance(result, Path)
    # The path should end with the project name
    assert result.name == "find_restaurants"


def test_load_config_file_success():
    """Test successful loading of config file content."""
    test_content = "test config content"
    mock_file = mock_open(read_data=test_content)
    
    with patch("builtins.open", mock_file):
        result = load_config_file("/absolute/path/config.txt", relative_to_project=False)
    
    assert result == test_content


def test_load_config_file_relative_path():
    """Test loading config file with relative path."""
    test_content = "relative config content"
    mock_file = mock_open(read_data=test_content)
    
    with patch("builtins.open", mock_file):
        with patch("src.utils.config_loader.get_project_root") as mock_root:
            mock_root.return_value = Path("/project/root")
            result = load_config_file("config/test.txt", relative_to_project=True)
    
    assert result == test_content


def test_load_config_file_not_found():
    """Test handling when config file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_config_file("/nonexistent/config.txt")
    
    assert result is None


# Integration-style Tests (using real temp files)

def test_load_urls_from_markdown_real_file(sample_markdown_content):
    """Test loading URLs from an actual temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_markdown_content)
        temp_path = f.name
    
    try:
        result = load_urls_from_markdown(temp_path)
        assert len(result) == 7
        assert all('eater.com' in url for url in result)
    finally:
        os.unlink(temp_path)  # Clean up


def test_load_urls_from_markdown_default_path():
    """Test using default path parameter."""
    mock_file = mock_open(read_data="- https://test.eater.com/default")
    
    with patch("builtins.open", mock_file):
        with patch("os.path.isabs", return_value=False):
            with patch.object(Path, "parent") as mock_parent:
                mock_root = Mock()
                mock_parent.parent.parent = mock_root
                mock_root.__truediv__ = Mock(return_value="/resolved/default/path")
                
                result = load_urls_from_markdown()  # Use default path
    
    assert len(result) == 1
    assert "https://test.eater.com/default" in result 