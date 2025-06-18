# Where to Eat

A Python project for scraping, pipelining, and displaying restaurant data from blogs.

## Prerequisites

- Python 3.13 or higher
- [direnv](https://direnv.net/) for environment management
- [Conda](https://docs.conda.io/en/latest/) for package management

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd google-maps-mcp
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
conda activate google-maps-mcp
```

## Project Structure

```
src/
├── main.py          # Main entry point
├── scrape/          # Scraping related code
├── utils/           # Utility functions
└── resources/       # Resource files
```

## Usage

[Add usage instructions here]

## Development

To run tests:
```bash
pytest
```

## TODOs

1. [ ] Migrate data storage to SQLite for better data persistence and querying capabilities
2. [ ] Have LLM review description and generate cuisine and vibe columns.
3. [ ] Add comprehensive documentation for each module
4. [ ] Implement error handling and logging
5. [ ] Add data validation and cleaning steps
6. [ ] Enrich with data from google maps API (hours?, Reviews? (https://developers.google.com/maps/documentation/javascript/place-reviews))

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
