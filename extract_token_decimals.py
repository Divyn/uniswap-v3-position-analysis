"""
Standalone script to extract token decimals from position data
"""
import json
import os
from datetime import datetime
from bitquery_client import BitqueryClient


def extract_token_addresses_from_positions(file_path: str) -> list:
    """Extract all unique token addresses from position data file"""
    print(f"Reading position data from: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    token_addresses = set()
    
    # Navigate through the data structure
    calls = data.get('data', {}).get('EVM', {}).get('Calls', [])
    
    for call in calls:
        returns = call.get('Returns', [])
        
        for return_item in returns:
            name = return_item.get('Name', '')
            value = return_item.get('Value', {})
            
            # Look for token0 and token1 addresses
            if name in ['token0', 'token1'] and 'address' in value:
                token_address = value['address']
                token_addresses.add(token_address)
                print(f"Found {name}: {token_address}")
    
    unique_tokens = list(token_addresses)
    print(f"\nExtracted {len(unique_tokens)} unique token addresses:")
    for i, token in enumerate(unique_tokens, 1):
        print(f"{i}. {token}")
    
    return unique_tokens


def save_token_decimals_to_file(token_data: dict, filename: str = "token_decimals.json") -> str:
    """Save token decimals data to file"""
    output_dir = "bitquery_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    full_filename = f"{filename}.json"
    filepath = os.path.join(output_dir, full_filename)
    
    with open(filepath, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"Saved token decimals to: {filepath}")
    return filepath


def create_token_decimals_lookup(file_path: str) -> dict:
    """Create a lookup dictionary for token address -> decimals"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    lookup = {}
    
    transfers = data.get('data', {}).get('EVM', {}).get('Transfers', [])
    
    for transfer in transfers:
        currency = transfer.get('Transfer', {}).get('Currency', {})
        address = currency.get('SmartContract')
        decimals = currency.get('Decimals')
        symbol = currency.get('Symbol')
        name = currency.get('Name')
        
        if address and decimals is not None:
            lookup[address] = {
                'decimals': decimals,
                'symbol': symbol,
                'name': name
            }
            print(f"Token: {symbol} ({name}) - Address: {address} - Decimals: {decimals}")
    
    return lookup


def main():
    """Main function to extract tokens and query decimals"""
    print("Starting token decimals extraction...")
    
    # Initialize Bitquery client
    client = BitqueryClient()
    
    # Find the most recent position data file
    response_dir = "bitquery_responses"
    position_files = [f for f in os.listdir(response_dir) if f.startswith("historical_positions_")]
    
    if not position_files:
        print("No position data files found!")
        print("Please run the main position tracking script first.")
        return
    
    # Use the most recent file
    latest_file = sorted(position_files)[-1]
    file_path = os.path.join(response_dir, latest_file)
    
    print(f"Using position data file: {latest_file}")
    
    try:
        # Step 1: Extract unique token addresses
        token_addresses = extract_token_addresses_from_positions(file_path)
        
        if not token_addresses:
            print("No token addresses found!")
            return
        
        # Step 2: Query token decimals
        print("\nQuerying token decimals...")
        decimals_response = client.get_token_decimals(token_addresses)
        
        # Step 3: Save response to file
        response_file = save_token_decimals_to_file(decimals_response)
        
        # Step 4: Create lookup dictionary
        print("\nCreating token decimals lookup...")
        lookup = create_token_decimals_lookup(response_file)
        
        # Step 5: Save lookup to separate file
        lookup_file = os.path.join(response_dir, f"token_decimals_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(lookup_file, 'w') as f:
            json.dump(lookup, f, indent=2)
        
        print(f"\nToken decimals lookup saved to: {lookup_file}")
        print(f"Found decimals for {len(lookup)} tokens")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
