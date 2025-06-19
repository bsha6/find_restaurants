import os
import pytest
from unittest import mock
import requests


@pytest.fixture
def mock_sqlite_env(tmp_path):
    """Mock the SQLITE_DATABASE_PATH environment variable to point to a temp file."""
    db_path = tmp_path / "test.db"
    with mock.patch.dict(os.environ, {"SQLITE_DATABASE_PATH": str(db_path)}):
        yield db_path

@pytest.fixture
def mock_sessionlocal():
    """Mock get_sessionlocal to avoid real DB connections."""
    with mock.patch("src.database.database.get_sessionlocal") as mock_session:
        yield mock_session

@pytest.fixture
def sample_json_ld():
    """Provide sample JSON-LD data for testing restaurant parsing."""
    return {
        "@type": "ItemList",
        "itemListElement": [
            {
                "item": {
                    "@type": "Restaurant",
                    "name": "Test Restaurant",
                    "url": "https://eater.com/test-restaurant#test-slug"
                }
            },
            {
                "item": {
                    "@type": "NotARestaurant",
                    "name": "Should Be Ignored"
                }
            }
        ]
    }

@pytest.fixture
def sample_html():
    """Provide sample HTML content for testing restaurant scraping."""
    return """
    <html>
        <script type="application/ld+json">
            {
                "@type": "ItemList",
                "itemListElement": [
                    {
                        "item": {
                            "@type": "Restaurant",
                            "name": "Test Restaurant",
                            "url": "https://eater.com/test-restaurant#test-slug"
                        }
                    }
                ]
            }
        </script>
        <div class="duet--article--map-card" data-slug="test-slug">
            <span class="hkfm3hg">123 Test St, Test City, TC 12345</span>
            <p class="duet--article--dangerously-set-cms-markup">A fantastic test restaurant.</p>
        </div>
    </html>
    """

@pytest.fixture
def mock_response(sample_html):
    """Provide a mock HTTP response for testing web requests."""
    mock_resp = mock.Mock(spec=requests.Response)
    mock_resp.text = sample_html
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "text/html"}
    return mock_resp 