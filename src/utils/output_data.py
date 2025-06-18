import pandas as pd
from pathlib import Path

def save_to_tsv(restaurants, output_file: str):
    """
    Save restaurant data to a TSV file.
    
    Args:
        restaurants (list): List of dictionaries containing restaurant data
        output_file (str): Path to output TSV file
    """
    # Get the project root directory (assuming this file is in src/scrape)
    project_root = Path(__file__).parent.parent
    
    # Create the resources/eater directory if it doesn't exist
    output_dir = project_root / 'resources' / 'eater'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct the full output path
    output_path = output_dir / output_file
    
    df = pd.DataFrame(restaurants)
    df.to_csv(output_path, index=False, sep='\t')
    print(f"Saved {len(restaurants)} restaurants to {output_path}")