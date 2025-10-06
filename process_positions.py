"""
Streamlined script to fetch positions, get token decimals, and convert amounts
"""
import json
from datetime import datetime, timedelta
from bitquery_client import BitqueryClient


def extract_token_addresses_from_positions_response(data: dict) -> list:
    """Extract all unique token addresses from position data response"""
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
    
    return list(token_addresses)


def query_token_decimals(client: BitqueryClient, token_addresses: list) -> dict:
    """Query token decimals for the given addresses"""
    print(f"Querying decimals for {len(token_addresses)} tokens...")
    return client.get_token_decimals(token_addresses)


def create_token_decimals_lookup(decimals_response: dict) -> dict:
    """Create a lookup dictionary for token address -> decimals"""
    lookup = {}
    
    transfers = decimals_response.get('data', {}).get('EVM', {}).get('Transfers', [])
    
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


def convert_amount(raw_amount: str, decimals: int) -> float:
    """Convert raw blockchain amount to actual token amount"""
    try:
        amount_int = int(raw_amount)
        return amount_int / (10 ** decimals)
    except (ValueError, TypeError):
        return 0.0


def calculate_price_from_tick(tick: int, token0_decimals: int, token1_decimals: int) -> float:
    """Calculate price from tick using the formula: price = (1.0001)^tick * 10^(decimals_token0 - decimals_token1)"""
    try:
        # Calculate (1.0001)^tick
        price_unadjusted = (1.0001) ** tick
        
        # Adjust for token decimals: 10^(decimals_token0 - decimals_token1)
        decimal_adjustment = 10 ** (token0_decimals - token1_decimals)
        
        # Final price = price_unadjusted * decimal_adjustment
        final_price = price_unadjusted * decimal_adjustment
        
        return final_price
    except (ValueError, TypeError, OverflowError):
        return 0.0


def process_positions_with_decimals(client: BitqueryClient, start_date: str = None, end_date: str = None, include_realtime: bool = True):
    """Main function to fetch positions and process with decimals"""
    all_positions = []
    
    # Step 1: Get historical positions
    print("Fetching historical positions...")
    historical_response = client.get_historical_positions(start_date, end_date)
    
    if historical_response.get('data', {}).get('EVM', {}).get('Calls'):
        historical_calls = historical_response.get('data', {}).get('EVM', {}).get('Calls', [])
        all_positions.extend(historical_calls)
        print(f"Found {len(historical_calls)} historical positions")
    
    # Step 2: Get real-time positions (if requested)
    if include_realtime:
        print("Fetching real-time positions...")
        realtime_response = client.get_recent_positions_realtime()
        
        if realtime_response.get('data', {}).get('EVM', {}).get('Calls'):
            realtime_calls = realtime_response.get('data', {}).get('EVM', {}).get('Calls', [])
            all_positions.extend(realtime_calls)
            print(f"Found {len(realtime_calls)} real-time positions")
    
    print(f"Total positions to process: {len(all_positions)}")
    
    if not all_positions:
        print("No position data found!")
        return
    
    # Create a combined response structure
    positions_response = {
        'data': {
            'EVM': {
                'Calls': all_positions
            }
        }
    }
    
    # DEBUG: Let's see what's actually in the response
    print("\n=== DEBUG: First position data ===")
    first_call = positions_response.get('data', {}).get('EVM', {}).get('Calls', [])[0]
    print("Arguments:", json.dumps(first_call.get('Arguments', []), indent=2))
    print("Returns:", json.dumps(first_call.get('Returns', []), indent=2))
    print("===================================\n")
    
    # Step 2: Extract token addresses
    print("Extracting token addresses...")
    token_addresses = extract_token_addresses_from_positions_response(positions_response)
    print(f"Found {len(token_addresses)} unique token addresses")
    
    # Step 3: Get token decimals
    decimals_response = query_token_decimals(client, token_addresses)
    token_decimals = create_token_decimals_lookup(decimals_response)
    
    if not token_decimals:
        print("No token decimals found!")
        return
    
    # Step 4: Process positions with converted amounts
    print("\nProcessing positions with converted amounts...")
    calls = positions_response.get('data', {}).get('EVM', {}).get('Calls', [])
    
    processed_positions = []
    
    for i, call in enumerate(calls):  # Process all positions
        if i < 5:  # Only show detailed output for first 5 positions
            print(f"\n--- Position {i+1} ---")
        elif i == 5:
            print(f"\n... Processing remaining {len(calls) - 5} positions silently ...")
        
        # Extract position data
        token_id = None
        token0_address = None
        token1_address = None
        liquidity = None
        fee = None
        tick_lower = None
        tick_upper = None
        
        # Get arguments (tokenId)
        arguments = call.get('Arguments', [])
        for arg in arguments:
            if arg.get('Name') == 'tokenId':
                token_id = arg.get('Value', {}).get('bigInteger')
                break
        
        # Get returns (token0, token1, liquidity, fee, ticks)
        returns = call.get('Returns', [])
        for return_item in returns:
            name = return_item.get('Name', '')
            value = return_item.get('Value', {})
            
            if name == 'token0' and 'address' in value:
                token0_address = value['address']
            elif name == 'token1' and 'address' in value:
                token1_address = value['address']
            elif name == 'liquidity' and 'bigInteger' in value:
                liquidity = value['bigInteger']
            elif name == 'fee' and 'bigInteger' in value:
                fee = value['bigInteger']
            elif name == 'tickLower' and 'bigInteger' in value:
                tick_lower = int(value['bigInteger'])
            elif name == 'tickUpper' and 'bigInteger' in value:
                tick_upper = int(value['bigInteger'])
        
        # Convert amounts using decimals
        token0_info = token_decimals.get(token0_address, {})
        token1_info = token_decimals.get(token1_address, {})
        
        token0_symbol = token0_info.get('symbol', 'Unknown')
        token1_symbol = token1_info.get('symbol', 'Unknown')
        token0_decimals = token0_info.get('decimals', 18)
        token1_decimals = token1_info.get('decimals', 18)
        
        # Keep liquidity as-is (L is dimensionless)
        
        # Calculate price bands from ticks
        price_lower = None
        price_upper = None
        if tick_lower is not None and tick_upper is not None:
            price_lower = calculate_price_from_tick(tick_lower, token0_decimals, token1_decimals)
            price_upper = calculate_price_from_tick(tick_upper, token0_decimals, token1_decimals)
        
        position_data = {
            'tokenId': token_id,
            'token0': {
                'address': token0_address,
                'symbol': token0_symbol,
                'decimals': token0_decimals
            },
            'token1': {
                'address': token1_address,
                'symbol': token1_symbol,
                'decimals': token1_decimals
            },
            'liquidity': liquidity,
            'fee': fee,
            'ticks': {
                'lower': tick_lower,
                'upper': tick_upper
            },
            'price_band': {
                'lower': price_lower,
                'upper': price_upper
            },
            'block': call.get('Block', {}).get('Number'),
            'timestamp': call.get('Block', {}).get('Time')
        }
        
        processed_positions.append(position_data)
        
        # Only show detailed output for first 5 positions
        if i < 5:
            print(f"Token ID: {token_id}")
            print(f"Token0: {token0_symbol} ({token0_address}) - Decimals: {token0_decimals}")
            print(f"Token1: {token1_symbol} ({token1_address}) - Decimals: {token1_decimals}")
            print(f"Liquidity: {liquidity}")
            print(f"Fee: {fee}")
            print(f"Tick Range: {tick_lower} to {tick_upper}")
            if price_lower is not None and price_upper is not None:
                print(f"Price Band: {price_lower:.6f} to {price_upper:.6f} {token1_symbol} per {token0_symbol}")
            else:
                print("Price Band: Unable to calculate")
    
    return processed_positions


def save_processed_positions_to_file(processed_positions: list, filename: str = "processed_positions.json") -> str:
    """Save processed positions to a JSON file"""
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    output_dir = "bitquery_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    full_filename = f"{filename}"
    filepath = os.path.join(output_dir, full_filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(processed_positions, f, indent=2)
    
    print(f"\n💾 Saved {len(processed_positions)} processed positions to: {filepath}")
    return filepath


def main(include_realtime=True):
    """Main function"""
    print("Starting combined position processing (historical + real-time)...")
    
    # Initialize Bitquery client
    client = BitqueryClient()
    
    try:
        # Set date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Format dates for Bitquery (YYYY-MM-DD)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        print(f"Historical data range: {start_date_str} to {end_date_str}")
        if include_realtime:
            print("Including real-time data")
        
        # Process both historical and real-time positions
        processed_positions = process_positions_with_decimals(client, start_date_str, end_date_str, include_realtime)
        
        if processed_positions:
            # Save processed positions to file
            filepath = save_processed_positions_to_file(processed_positions)
            print(f"\n✅ Successfully processed {len(processed_positions)} positions!")
            print(f"📁 Results saved to: {filepath}")
        else:
            print("\n❌ No positions were processed!")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
