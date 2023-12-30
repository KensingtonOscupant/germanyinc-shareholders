import pandas as pd
import requests
import argparse
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()

pi_key = os.getenv("OPENCORPORATES_API_KEY")

# Set up argparse to accept command-line arguments for slice indices
parser = argparse.ArgumentParser(description='Process a slice of a DataFrame with the Reconciliation API.')
parser.add_argument('--start', type=int, help='Start index of the DataFrame slice', required=True)
parser.add_argument('--end', type=int, help='End index of the DataFrame slice', required=True)
args = parser.parse_args()

# Read the original dataframe
original_df = pd.read_csv('data/231228_shareholders_legal_entities.csv')

# Select the slice of the DataFrame based on provided arguments
df_slice = original_df[args.start:args.end]

def query_main_api(company_name):
    url = f"https://api.opencorporates.com/v0.4/companies/search?q={company_name}&api_token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Create an empty DataFrame for the results
reconciled_df = pd.DataFrame(columns=['original_id', 'result_id', 'name', 'OpenCorporates_url'])

# Temporary storage for new rows
new_rows = []

counter = 0

# Iterate over the selected slice of the DataFrame with a progress bar
for index, row in tqdm(df_slice.iterrows(), total=df_slice.shape[0]):
    counter += 1
    api_response = query_main_api(row['notifying_party'])
    if api_response and 'results' in api_response and 'companies' in api_response['results']:
        for result_id, company in enumerate(api_response['results']['companies']):
            company_data = company['company']
            # Process current, previous, and alternative names
            for name in [company_data.get('name')] + [n['company_name'] for n in company_data.get('previous_names', [])] + company_data.get('alternative_names', []):
                if name:
                    new_row = {
                        'original_id': row['original_id'],
                        'result_id': result_id + 1,
                        'name': name,
                        'OpenCorporates_url': company_data.get('opencorporates_url')
                    }
                    new_rows.append(new_row)
    
    if counter % 100 == 0:
        # Concatenate the new data to the DataFrame
        reconciled_df = pd.concat([reconciled_df, pd.DataFrame(new_rows)], ignore_index=True)
        new_rows = []  # Reset the list
        reconciled_df.to_csv(f'data/output_data/231229_main_reconciled_data_temp.csv', index=False)
        print(f"Data saved to CSV after processing {index} rows.")

# Concatenate any remaining data
if new_rows:
    reconciled_df = pd.concat([reconciled_df, pd.DataFrame(new_rows)], ignore_index=True)

reconciled_df.to_csv('data/output_data/231229_main_reconciled_data_final.csv', index=False)
print("Final data saved to CSV.")
