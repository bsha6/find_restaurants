import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from src.database.database import get_db
from src.database import crud
import logging
import json
import tldextract

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_restaurant_data(html_content: str, url: str):
    """
    Extract restaurant data from Eater blog HTML content using JSON-LD data.
    
    Args:
        html_content (str): HTML content of the Eater blog post
        
    Returns:
        list: List of dictionaries containing restaurant data
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    restaurants = []
    
    # Find the JSON-LD script tag
    script_tag = soup.find('script', type='application/ld+json')
    if not script_tag:
        logger.error("No JSON-LD data found in the page")
        return restaurants
    
    try:
        # Parse the JSON-LD data
        json_data = json.loads(script_tag.string)
        logger.info(f"Successfully parsed JSON-LD data with {len(json_data.get('itemListElement', []))} items")
        
        # Extract restaurant data from the itemListElement
        if 'itemListElement' in json_data:
            for item in json_data['itemListElement']:
                if 'item' in item and item['item']['@type'] == 'Restaurant':
                    restaurant = item['item']
                    logger.info(f"Processing restaurant: {restaurant.get('name')}")
                    
                    # Find the address for this restaurant
                    address = None
                    description = None
                    # Look for the map card div with the restaurant's data-slug
                    map_card = soup.find('div', {'class': 'duet--article--map-card', 'data-slug': restaurant.get('url', '').split('#')[-1]})
                    if map_card:
                        logger.info(f"Found map card for {restaurant.get('name')}")
                        # Find the address span within the map card
                        address_span = map_card.find('span', {'class': 'hkfm3hg'})
                        if address_span:
                            address = address_span.text.strip()
                            logger.info(f"Found address for {restaurant.get('name')}: {address}")
                        else:
                            logger.warning(f"No address span found in map card for {restaurant.get('name')}")
                        
                        # Find all description paragraphs within the map card
                        description_paragraphs = map_card.find_all('p', {'class': 'duet--article--dangerously-set-cms-markup'})
                        if description_paragraphs:
                            description = ' '.join([p.text.strip() for p in description_paragraphs])
                            logger.info(f"Found description for {restaurant.get('name')}")
                        else:
                            logger.warning(f"No description found for {restaurant.get('name')}")
                    else:
                        logger.warning(f"No map card found for {restaurant.get('name')} with data-slug: {restaurant.get('url', '').split('#')[-1]}")
                    
                    if not address:
                        logger.warning(f"Skipping restaurant {restaurant.get('name')} - no address found")
                        continue
                        
                    restaurants.append({
                        'name': restaurant.get('name'),
                        'description': description,
                        'source': tldextract.extract(restaurant.get('url', '')).domain,
                        'source_url': restaurant.get('url', ''),
                        'address': address,
                    })
                    logger.info(f"Successfully added restaurant: {restaurant.get('name')}")
        
        logger.info(f"Successfully extracted {len(restaurants)} restaurants from JSON-LD data")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON-LD data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error extracting restaurant data: {e}")
    
    return restaurants

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def scrape_eater_blog(url: str):
    """
    Scrape restaurant data from an Eater blog post.
    
    Args:
        url (str): URL of the Eater blog post
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
        
        # Debug: Print response status and headers
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Debug: Save HTML to file for inspection
        with open('debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Saved HTML response to debug_response.html")
        
        restaurants = extract_restaurant_data(response.text, url)
        logger.info(f"Found {len(restaurants)} restaurants")
        
        # Save to database
        db = next(get_db())
        for restaurant in restaurants:
            # Check if restaurant already exists by address
            existing = crud.get_restaurant_by_address(db, restaurant['address'])
            if existing:
                # Update existing restaurant
                logger.info(f"Updating existing restaurant at address {restaurant['address']}: {restaurant['name']}")
                crud.update_restaurant(db, existing.id, restaurant)
            else:
                # Create new restaurant
                logger.info(f"Creating new restaurant: {restaurant['name']} at {restaurant['address']}")
                crud.create_restaurant(db, restaurant)
        
        return restaurants
    except requests.RequestException as e:
        logger.error(f"Error scraping {url}: {e}")
        raise  # Re-raise the exception to trigger retry
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    urls = [
        # "https://dc.eater.com/maps/dc-best-restaurants-38",
        "https://www.eater.com/maps/best-new-restaurants-columbus-ohio",
        "https://dc.eater.com/maps/best-new-restaurants-heatmap-dc"
    ]
    for url in urls:
        try:
            restaurants = scrape_eater_blog(url)
            logger.info(f"Successfully processed {len(restaurants)} restaurants from {url}")
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
