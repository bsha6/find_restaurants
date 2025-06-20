import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import json
import tldextract
import concurrent.futures
import time

from src.database.database import get_db
from src.database import crud


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_json_ld(soup: BeautifulSoup) -> dict | None:
    """
    Parse the JSON-LD script tag from the BeautifulSoup object.
    Args:
        soup (BeautifulSoup): Parsed HTML soup.
    Returns:
        dict | None: Parsed JSON-LD data or None if not found/invalid.
    """
    script_tag = soup.find('script', type='application/ld+json')
    if not script_tag:
        logger.error("No JSON-LD data found in the page")
        return None
    json_text = script_tag.get_text(strip=True)
    if not json_text:
        logger.error("JSON-LD script tag is empty")
        return None
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON-LD data: {e}")
        return None


def get_restaurant_items(json_data: dict) -> list[dict]:
    """
    Extract restaurant items from JSON-LD data.
    Args:
        json_data (dict): Parsed JSON-LD data.
    Returns:
        list[dict]: List of restaurant item dicts.
    """
    items = []
    if not json_data or 'itemListElement' not in json_data:
        return items
    for item in json_data['itemListElement']:
        if 'item' in item and item['item'].get('@type') == 'Restaurant':
            items.append(item['item'])
    return items


def extract_map_card_info(soup: BeautifulSoup, restaurant: dict) -> tuple[str | None, str | None]:
    """
    Extract address and description from the map card for a restaurant.
    Args:
        soup (BeautifulSoup): Parsed HTML soup.
        restaurant (dict): Restaurant item dict.
    Returns:
        tuple[str | None, str | None]: (address, description)
    """
    address = None
    description = None
    map_card = soup.find('div', {'class': 'duet--article--map-card', 'data-slug': restaurant.get('url', '').split('#')[-1]})
    if isinstance(map_card, Tag):
        address_span = map_card.find('span', class_='hkfm3hg')
        if address_span:
            address = address_span.text.strip()
        description_paragraphs = map_card.find_all('p', class_='duet--article--dangerously-set-cms-markup')
        if description_paragraphs:
            description = ' '.join([p.text.strip() for p in description_paragraphs])
    return address, description


def build_restaurant_dict(restaurant: dict, address: str, description: str | None) -> dict:
    """
    Build a dictionary representing a restaurant.
    Args:
        restaurant (dict): Restaurant item dict.
        address (str): Restaurant address.
        description (str | None): Restaurant description.
    Returns:
        dict: Restaurant dictionary for output/storage.
    """
    return {
        'name': restaurant.get('name'),
        'description': description,
        'source': tldextract.extract(restaurant.get('url', '')).domain,
        'source_url': restaurant.get('url', ''),
        'address': address,
    }


def extract_restaurant_data(html_content: str, url: str) -> list[dict]:
    """
    Extract restaurant data from Eater blog HTML content using JSON-LD data.
    Args:
        html_content (str): HTML content of the Eater blog post.
        url (str): URL of the Eater blog post.
    Returns:
        list[dict]: List of dictionaries containing restaurant data.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    restaurants = []
    json_data = parse_json_ld(soup)
    if not json_data:
        return restaurants
    logger.info(f"Successfully parsed JSON-LD data with {len(json_data.get('itemListElement', []))} items")
    for restaurant in get_restaurant_items(json_data):
        logger.info(f"Processing restaurant: {restaurant.get('name')}")
        address, description = extract_map_card_info(soup, restaurant)
        if not address:
            logger.warning(f"Skipping restaurant {restaurant.get('name')} - no address found")
            continue
        restaurant_dict = build_restaurant_dict(restaurant, address, description)
        restaurants.append(restaurant_dict)
        logger.info(f"Successfully added restaurant: {restaurant.get('name')}")
    logger.info(f"Successfully extracted {len(restaurants)} restaurants from JSON-LD data")
    return restaurants

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def scrape_eater_blog(url: str) -> list[dict]:
    """
    Scrape restaurant data from an Eater blog post.
    Args:
        url (str): URL of the Eater blog post.
    Returns:
        list[dict]: List of dictionaries containing restaurant data.
    """
    try:
        logger.info(f"Starting to scrape: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        logger.debug(f"Response text (first 500 chars): {response.text[:500]}")
        logger.info("Saved HTML response to debug_response.html")
        restaurants = extract_restaurant_data(response.text, url)
        logger.info(f"Found {len(restaurants)} restaurants")
        with get_db() as db:
            for restaurant in restaurants:
                existing = crud.get_restaurant_by_address(db, restaurant['address'])
                if existing:
                    logger.info(f"Updating existing restaurant at address {restaurant['address']}: {restaurant['name']}")
                    crud.update_restaurant(db, existing.id, restaurant) # type: ignore
                else:
                    logger.info(f"Creating new restaurant: {restaurant['name']} at {restaurant['address']}")
                    crud.create_restaurant(db, restaurant)
        return restaurants
    except requests.RequestException as e:
        logger.error(f"Error scraping {url}: {e}")
        raise  # Re-raise the exception to trigger retry
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def scrape_eater_blogs_concurrently(urls: list[str], max_workers: int = 5):
    """
    Scrape multiple Eater blog posts concurrently.
    Args:
        urls (list[str]): A list of Eater blog post URLs to scrape.
        max_workers (int): The maximum number of threads to use.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_eater_blog, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                restaurants = future.result()
                logger.info(f"Successfully processed {len(restaurants)} restaurants from {url}")
            except Exception as exc:
                logger.error(f'{url} generated an exception: {exc}')
        
        # Explicitly shutdown the executor and wait for threads to finish
        executor.shutdown(wait=True)
    
    # Give threads a moment to fully clean up before interpreter shutdown
    time.sleep(0.1)
    logger.info("All threads completed and cleaned up successfully")

if __name__ == "__main__":
    urls_to_scrape = [
        # "https://dc.eater.com/maps/dc-best-restaurants-38",
        # "https://www.eater.com/maps/best-new-restaurants-columbus-ohio",
        # "https://dc.eater.com/maps/best-new-restaurants-heatmap-dc",
        "https://sf.eater.com/maps/best-restaurants-san-francisco-38",
        "https://sf.eater.com/maps/best-new-restaurants-san-francisco",
        "https://sf.eater.com/maps/best-sushi-restaurants-omakase-san-francisco"
    ]
    scrape_eater_blogs_concurrently(urls_to_scrape)
