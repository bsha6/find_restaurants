import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import requests
from src.scrape.eater_blog import (
    parse_json_ld,
    get_restaurant_items,
    extract_map_card_info,
    build_restaurant_dict,
    extract_restaurant_data,
    scrape_eater_blog,
)
import json


# Happy Path Tests

def test_parse_json_ld_success(sample_html):
    """Test successful parsing of JSON-LD data from HTML."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    result = parse_json_ld(soup)
    assert result is not None
    assert result["@type"] == "ItemList"
    assert len(result["itemListElement"]) == 1

def test_get_restaurant_items_success(sample_json_ld):
    """Test successful extraction of restaurant items from JSON-LD data."""
    result = get_restaurant_items(sample_json_ld)
    assert len(result) == 1
    assert result[0]["name"] == "Test Restaurant"

def test_extract_map_card_info_success(sample_html):
    """Test successful extraction of address and description from map card."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    restaurant = {"url": "https://eater.com/test-restaurant#test-slug"}
    address, description = extract_map_card_info(soup, restaurant)
    assert address == "123 Test St, Test City, TC 12345"
    assert description == "A fantastic test restaurant."

def test_build_restaurant_dict():
    """Test building restaurant dictionary with all fields."""
    restaurant = {
        "name": "Test Restaurant",
        "url": "https://eater.com/test-restaurant"
    }
    address = "123 Test St"
    description = "Test Description"
    result = build_restaurant_dict(restaurant, address, description)
    assert result["name"] == "Test Restaurant"
    assert result["address"] == "123 Test St"
    assert result["description"] == "Test Description"
    assert result["source"] == "eater"
    assert result["source_url"] == "https://eater.com/test-restaurant"

def test_extract_restaurant_data_success(sample_html):
    """Test successful extraction of restaurant data from HTML content."""
    # Use the same domain as in the restaurant URL to test source extraction
    test_url = "https://eater.com/test-article"
    result = extract_restaurant_data(sample_html, test_url)
    
    assert len(result) == 1
    restaurant = result[0]
    # Test all fields from the restaurant dictionary
    assert restaurant["name"] == "Test Restaurant"
    assert restaurant["address"] == "123 Test St, Test City, TC 12345"
    assert restaurant["description"] == "A fantastic test restaurant."
    # The source should come from the input URL, not the restaurant URL
    assert restaurant["source"] == "eater"
    # The source_url should come from the JSON-LD data
    assert restaurant["source_url"] == "https://eater.com/test-restaurant#test-slug"

def test_extract_restaurant_data_no_json_ld():
    """Test handling of HTML content with no JSON-LD data."""
    html = "<html><body>No JSON-LD here</body></html>"
    result = extract_restaurant_data(html, "https://test.eater.com")
    assert len(result) == 0

def test_extract_restaurant_data_mixed_items(sample_json_ld):
    """Test handling of JSON-LD data with mixed restaurant and non-restaurant items."""
    html = f"""
    <html>
        <script type="application/ld+json">
            {json.dumps(sample_json_ld)}
        </script>
        <div class="duet--article--map-card" data-slug="test-slug">
            <span class="hkfm3hg">123 Test St, Test City, TC 12345</span>
            <p class="duet--article--dangerously-set-cms-markup">A fantastic test restaurant.</p>
        </div>
    </html>
    """
    result = extract_restaurant_data(html, "https://test.eater.com")
    assert len(result) == 1  # Should only get the restaurant, not the NotARestaurant
    assert result[0]["name"] == "Test Restaurant"

def test_extract_restaurant_data_missing_address(sample_json_ld):
    """Test handling of restaurant with missing address."""
    html = f"""
    <html>
        <script type="application/ld+json">
            {json.dumps(sample_json_ld)}
        </script>
        <div class="duet--article--map-card" data-slug="test-slug">
            <p class="duet--article--dangerously-set-cms-markup">Description without address.</p>
        </div>
    </html>
    """
    result = extract_restaurant_data(html, "https://test.eater.com")
    assert len(result) == 0

@patch("requests.get")
def test_scrape_eater_blog_success(mock_get, mock_response, mock_sessionlocal):
    """Test successful scraping of Eater blog."""
    mock_get.return_value = mock_response
    mock_db = Mock()
    mock_sessionlocal.return_value = Mock()
    mock_sessionlocal.return_value.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = scrape_eater_blog("https://test.eater.com/test-article")
    assert len(result) == 1
    assert result[0]["name"] == "Test Restaurant"
    assert result[0]["address"] == "123 Test St, Test City, TC 12345"

# Edge Cases and Error Tests

def test_parse_json_ld_empty_script():
    """Test handling of empty JSON-LD script tag."""
    html = '<script type="application/ld+json"></script>'
    soup = BeautifulSoup(html, 'html.parser')
    result = parse_json_ld(soup)
    assert result is None

def test_parse_json_ld_invalid_json():
    """Test handling of invalid JSON in script tag."""
    html = '<script type="application/ld+json">{"invalid": json</script>'
    soup = BeautifulSoup(html, 'html.parser')
    result = parse_json_ld(soup)
    assert result is None

def test_get_restaurant_items_no_items():
    """Test handling of JSON-LD data with no restaurant items."""
    json_data = {"itemListElement": [{"item": {"@type": "NotARestaurant"}}]}
    result = get_restaurant_items(json_data)
    assert len(result) == 0

def test_extract_map_card_info_missing_data(sample_html):
    """Test handling of missing address or description in map card."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    restaurant = {"url": "nonexistent-slug"}
    address, description = extract_map_card_info(soup, restaurant)
    assert address is None
    assert description is None

@patch("requests.get")
def test_scrape_eater_blog_http_error(mock_get):
    """Test handling of HTTP errors during scraping."""
    mock_get.side_effect = requests.RequestException("Test error")
    with pytest.raises(requests.RequestException):
        scrape_eater_blog("https://test.eater.com/test-article")

@patch("requests.get")
def test_scrape_eater_blog_retry_success(mock_get, mock_response, mock_sessionlocal):
    """Test successful retry after initial failure."""
    mock_get.side_effect = [
        requests.RequestException("Test error"),
        mock_response
    ]
    mock_db = Mock()
    mock_sessionlocal.return_value = Mock()
    mock_sessionlocal.return_value.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = scrape_eater_blog("https://test.eater.com/test-article")
    assert len(result) == 1
    assert mock_get.call_count == 2  # Verify retry happened 