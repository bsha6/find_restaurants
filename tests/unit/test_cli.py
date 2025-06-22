from click.testing import CliRunner
from unittest import mock
import tempfile
import os

from src.main import cli, config


class TestCLI:
    """Test cases for the CLI interface."""
    
    def test_cli_help(self):
        """Test that CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Restaurant Data Collection CLI' in result.output
        assert 'scrape' in result.output
        assert 'export' in result.output
        assert 'config' in result.output
    
    def test_scrape_help(self):
        """Test scrape command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['scrape', '--help'])
        assert result.exit_code == 0
        assert 'Scrape restaurant data' in result.output
        assert '--workers' in result.output
        assert '--delay' in result.output
    
    def test_config_show(self):
        """Test config show command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        assert 'max_workers' in result.output
        assert 'default_urls' in result.output
    
    def test_config_set_simple_value(self):
        """Test setting a simple configuration value."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_config.json')
            
            # Mock the config file path
            with mock.patch.object(config, 'config_file', config_file):
                runner = CliRunner()
                result = runner.invoke(cli, ['config', 'set', 'max_workers', '10'])
                assert result.exit_code == 0
                assert 'Set max_workers = 10' in result.output
    
    def test_config_set_list_value(self):
        """Test setting a list configuration value."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_config.json')
            
            with mock.patch.object(config, 'config_file', config_file):
                runner = CliRunner()
                result = runner.invoke(cli, ['config', 'set', 'default_urls', 'url1,url2,url3'])
                assert result.exit_code == 0
                assert 'Set default_urls = ' in result.output
    
    @mock.patch('src.main.setup_database')
    def test_init_command(self, mock_setup_db):
        """Test initialization command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_config.json')
            
            with mock.patch.object(config, 'config_file', config_file):
                runner = CliRunner()
                result = runner.invoke(cli, ['init'])
                assert result.exit_code == 0
                assert 'Initialization complete!' in result.output
                mock_setup_db.assert_called_once()
    
    @mock.patch('src.main.get_db')
    @mock.patch('src.main.crud.get_restaurants')
    def test_export_no_restaurants(self, mock_get_restaurants, mock_get_db):
        """Test export command when no restaurants exist."""
        # Mock empty restaurant list
        mock_get_restaurants.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['export'])
        assert result.exit_code == 1
        assert 'No restaurants found in database' in result.output
    
    @mock.patch('src.main.get_db')
    @mock.patch('src.main.crud.get_restaurants')
    def test_list_no_restaurants(self, mock_get_restaurants, mock_get_db):
        """Test list command when no restaurants exist."""
        mock_get_restaurants.return_value = []
        
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert 'No restaurants found' in result.output
    
    def test_scrape_no_urls_no_defaults(self):
        """Test scrape command with no URLs and no defaults."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'test_config.json')
            
            # Create config with empty default_urls
            test_config = config.default_config.copy()
            test_config['default_urls'] = []
            
            with mock.patch.object(config, 'config_file', config_file):
                with mock.patch.object(config, 'config', test_config):
                    runner = CliRunner()
                    result = runner.invoke(cli, ['scrape'])
                    assert result.exit_code == 1
                    assert 'No URLs provided' in result.output
    
    @mock.patch('src.main.get_db')
    @mock.patch('src.main.crud.get_restaurants')
    @mock.patch('src.main.scrape_eater_blog')
    @mock.patch('src.main.setup_database')
    def test_scrape_single_url(self, mock_setup_db, mock_scrape, mock_get_restaurants, mock_get_db):
        """Test scraping a single URL."""
        mock_scrape.return_value = [{'name': 'Test Restaurant'}]
        mock_get_restaurants.return_value = [mock.Mock(name='Test Restaurant')]
        
        runner = CliRunner()
        result = runner.invoke(cli, ['scrape', 'https://example.com/test'])
        
        # Should not exit with error
        assert result.exit_code == 0
        assert 'Starting restaurant scraping' in result.output
        mock_setup_db.assert_called_once()
        mock_scrape.assert_called_once()
    
    @mock.patch('src.main.get_db')
    @mock.patch('src.main.crud.get_restaurants')
    def test_status_command(self, mock_get_restaurants, mock_get_db):
        """Test status command."""
        # Mock some restaurants
        from unittest.mock import Mock
        mock_restaurant = Mock()
        mock_restaurant.name = "Test Restaurant"
        mock_restaurant.source = "eater"
        mock_get_restaurants.return_value = [mock_restaurant]
        
        runner = CliRunner()
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert 'Restaurant Scraper Status' in result.output
        assert 'Total restaurants: 1' in result.output


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test that configuration initializes properly."""
        cfg = config
        assert cfg.default_config['max_workers'] == 5
        assert 'default_urls' in cfg.default_config
        assert cfg.default_config['rate_limit_delay'] == 1.0
    
    def test_config_get_set(self):
        """Test getting and setting configuration values."""
        cfg = config
        original_value = cfg.get('max_workers')
        
        cfg.set('max_workers', 10)
        assert cfg.get('max_workers') == 10
        
        # Restore original value
        cfg.set('max_workers', original_value) 