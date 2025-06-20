import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import requests
import json

from src.scrape.eater_blog import (
    parse_json_ld,
    get_restaurant_items,
    extract_map_card_info,
    build_restaurant_dict,
    extract_restaurant_data,
    scrape_eater_blog,
    scrape_eater_blogs_concurrently,
)


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


# Concurrent Scraping Tests

@patch("src.scrape.eater_blog.scrape_eater_blog")
def test_scrape_eater_blogs_concurrently_success(mock_scrape_single):
    """Test successful concurrent scraping of multiple URLs."""
    # Mock successful results for each URL
    mock_scrape_single.side_effect = [
        [{"name": "Restaurant 1", "address": "Address 1"}],
        [{"name": "Restaurant 2", "address": "Address 2"}],
        [{"name": "Restaurant 3", "address": "Address 3"}]
    ]
    
    urls = [
        "https://test.eater.com/url1",
        "https://test.eater.com/url2", 
        "https://test.eater.com/url3"
    ]
    
    # Should not raise any exceptions
    scrape_eater_blogs_concurrently(urls, max_workers=2)
    
    # Verify each URL was called
    assert mock_scrape_single.call_count == 3
    called_urls = [call[0][0] for call in mock_scrape_single.call_args_list]
    assert set(called_urls) == set(urls)

@patch("src.scrape.eater_blog.scrape_eater_blog")
def test_scrape_eater_blogs_concurrently_with_failures(mock_scrape_single):
    """Test concurrent scraping when some URLs fail."""
    # Mock mixed success and failure results
    mock_scrape_single.side_effect = [
        [{"name": "Restaurant 1", "address": "Address 1"}],  # Success
        requests.RequestException("Network error"),          # Failure
        [{"name": "Restaurant 3", "address": "Address 3"}]   # Success
    ]
    
    urls = [
        "https://test.eater.com/url1",
        "https://test.eater.com/url2", 
        "https://test.eater.com/url3"
    ]
    
    # Should not raise exceptions even when individual URLs fail
    scrape_eater_blogs_concurrently(urls, max_workers=2)
    
    # Verify all URLs were attempted
    assert mock_scrape_single.call_count == 3

@patch("src.scrape.eater_blog.scrape_eater_blog")
def test_scrape_eater_blogs_concurrently_empty_list(mock_scrape_single):
    """Test concurrent scraping with empty URL list."""
    scrape_eater_blogs_concurrently([])
    
    # Should not call scrape_eater_blog at all
    assert mock_scrape_single.call_count == 0

@patch("src.scrape.eater_blog.scrape_eater_blog")
def test_scrape_eater_blogs_concurrently_single_url(mock_scrape_single):
    """Test concurrent scraping with single URL."""
    mock_scrape_single.return_value = [{"name": "Solo Restaurant", "address": "Solo Address"}]
    
    urls = ["https://test.eater.com/single-url"]
    
    scrape_eater_blogs_concurrently(urls, max_workers=1)
    
    assert mock_scrape_single.call_count == 1
    assert mock_scrape_single.call_args[0][0] == urls[0]

@patch("src.scrape.eater_blog.scrape_eater_blog")
def test_scrape_eater_blogs_concurrently_custom_max_workers(mock_scrape_single):
    """Test concurrent scraping with custom max_workers parameter."""
    mock_scrape_single.side_effect = [
        [{"name": f"Restaurant {i}", "address": f"Address {i}"}] 
        for i in range(10)
    ]
    
    urls = [f"https://test.eater.com/url{i}" for i in range(10)]
    
    # Test with different worker counts
    scrape_eater_blogs_concurrently(urls, max_workers=3)
    
    assert mock_scrape_single.call_count == 10

@patch("src.scrape.eater_blog.scrape_eater_blog")
@patch("src.scrape.eater_blog.logger")
def test_scrape_eater_blogs_concurrently_logs_results(mock_logger, mock_scrape_single):
    """Test that concurrent scraping logs success and failure messages."""
    mock_scrape_single.side_effect = [
        [{"name": "Restaurant 1"}],              # Success
        requests.RequestException("Test error")  # Failure
    ]
    
    urls = ["https://test.eater.com/success", "https://test.eater.com/failure"]
    
    scrape_eater_blogs_concurrently(urls)
    
    # Check that both success and error messages were logged
    info_calls = [call for call in mock_logger.info.call_args_list]
    error_calls = [call for call in mock_logger.error.call_args_list]
    
    # Should have success log for the working URL
    success_logged = any("Successfully processed 1 restaurants" in str(call) for call in info_calls)
    assert success_logged
    
    # Should have error log for the failing URL
    error_logged = any("generated an exception" in str(call) for call in error_calls)
    assert error_logged

@patch("src.scrape.eater_blog.scrape_eater_blog") 
def test_scrape_eater_blogs_concurrently_all_failures(mock_scrape_single):
    """Test concurrent scraping when all URLs fail."""
    mock_scrape_single.side_effect = [
        requests.RequestException("Error 1"),
        requests.RequestException("Error 2"),
        requests.RequestException("Error 3")
    ]
    
    urls = [
        "https://test.eater.com/fail1",
        "https://test.eater.com/fail2",
        "https://test.eater.com/fail3"
    ]
    
    # Should handle all failures gracefully without raising
    scrape_eater_blogs_concurrently(urls)
    
    # All URLs should have been attempted
    assert mock_scrape_single.call_count == 3 