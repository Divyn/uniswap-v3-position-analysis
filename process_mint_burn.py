"""
Process Uniswap V3 mint and burn events to analyze liquidity events
"""
import json
import os
from datetime import datetime, timedelta
from bitquery_client import BitqueryClient


def extract_token_addresses_from_mint_burn_response(data: dict) -> list:
    """Extract all unique token addresses from mint/burn data response"""
    token_addresses = set()
    
    # Navigate through the data structure
    calls = data.get('data', {}).get('EVM', {}).get('Calls', [])
    
    for call in calls:
        arguments = call.get('Arguments', [])
        
        for arg in arguments:
            name = arg.get('Name', '')
            value = arg.get('Value', {})
            
            # Look for token addresses in mint/burn parameters
            # token0 and token1 are typically in the first two arguments
            if name.startswith('INonfungiblePositionManagerMintParams') and 'address' in value:
                token_address = value['address']
                token_addresses.add(token_address)
    
    return list(token_addresses)


def parse_mint_burn_arguments(arguments: list) -> dict:
    """Parse mint/burn function arguments to extract position parameters"""
    params = {}
    
    for arg in arguments:
        index = arg.get('Index', -1)
        value = arg.get('Value', {})
        
        # Based on the sample data structure:
        # Index 0: token0 address
        # Index 1: token1 address  
        # Index 2: fee tier
        # Index 3: tickLower
        # Index 4: tickUpper
        # Index 5: amount0Desired
        # Index 6: amount0Min
        # Index 7: amount1Desired
        # Index 8: amount1Min
        # Index 9: recipient
        # Index 10: deadline
        
        if index == 0 and 'address' in value:
            params['token0'] = value['address']
        elif index == 1 and 'address' in value:
            params['token1'] = value['address']
        elif index == 2 and 'bigInteger' in value:
            params['fee'] = value['bigInteger']
        elif index == 3 and 'bigInteger' in value:
            params['tickLower'] = int(value['bigInteger'])
        elif index == 4 and 'bigInteger' in value:
            params['tickUpper'] = int(value['bigInteger'])
        elif index == 5 and 'bigInteger' in value:
            params['amount0Desired'] = value['bigInteger']
        elif index == 6 and 'bigInteger' in value:
            params['amount0Min'] = value['bigInteger']
        elif index == 7 and 'bigInteger' in value:
            params['amount1Desired'] = value['bigInteger']
        elif index == 8 and 'bigInteger' in value:
            params['amount1Min'] = value['bigInteger']
        elif index == 9 and 'address' in value:
            params['recipient'] = value['address']
        elif index == 10 and 'bigInteger' in value:
            params['deadline'] = value['bigInteger']
    
    return params


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


def process_mint_events_with_decimals(client: BitqueryClient, start_date: str = None, end_date: str = None, include_realtime: bool = True):
    """Main function to fetch mint events and process with decimals"""
    all_events = []
    
    # Step 1: Get historical mint events
    print("Fetching historical mint events...")
    historical_response = client.get_historical_mint_events(start_date, end_date)
    
    if historical_response.get('data', {}).get('EVM', {}).get('Calls'):
        historical_calls = historical_response.get('data', {}).get('EVM', {}).get('Calls', [])
        all_events.extend(historical_calls)
        print(f"Found {len(historical_calls)} historical mint events")
    
    # Step 2: Get real-time mint events (if requested)
    if include_realtime:
        print("Fetching real-time mint events...")
        realtime_response = client.get_recent_mint_events_realtime()
        
        if realtime_response.get('data', {}).get('EVM', {}).get('Calls'):
            realtime_calls = realtime_response.get('data', {}).get('EVM', {}).get('Calls', [])
            all_events.extend(realtime_calls)
            print(f"Found {len(realtime_calls)} real-time mint events")
    
    print(f"Total mint events to process: {len(all_events)}")
    
    if not all_events:
        print("No mint event data found!")
        return
    
    # Create a combined response structure
    events_response = {
        'data': {
            'EVM': {
                'Calls': all_events
            }
        }
    }
    
    # DEBUG: Let's see what's actually in the response
    print("\n=== DEBUG: First mint event data ===")
    first_call = events_response.get('data', {}).get('EVM', {}).get('Calls', [])[0]
    print("Arguments:", json.dumps(first_call.get('Arguments', []), indent=2))
    print("Call Signature:", first_call.get('Call', {}).get('Signature', {}).get('Name'))
    print("===================================\n")
    
    # Step 2: Extract token addresses
    print("Extracting token addresses...")
    token_addresses = extract_token_addresses_from_mint_burn_response(events_response)
    print(f"Found {len(token_addresses)} unique token addresses")
    
    # Step 3: Get token decimals
    from process_positions import query_token_decimals, create_token_decimals_lookup
    decimals_response = query_token_decimals(client, token_addresses)
    token_decimals = create_token_decimals_lookup(decimals_response)
    
    if not token_decimals:
        print("No token decimals found!")
        return
    
    # Step 4: Process mint events with converted amounts
    print("\nProcessing mint events with converted amounts...")
    calls = events_response.get('data', {}).get('EVM', {}).get('Calls', [])
    
    processed_events = []
    
    for i, call in enumerate(calls):
        if i < 5:  # Only show detailed output for first 5 events
            print(f"\n--- Mint Event {i+1} ---")
        elif i == 5:
            print(f"\n... Processing remaining {len(calls) - 5} events silently ...")
        
        # Extract event type (should be 'mint' for all events now)
        event_type = call.get('Call', {}).get('Signature', {}).get('Name', 'mint')
        
        # Parse arguments to get position parameters
        arguments = call.get('Arguments', [])
        params = parse_mint_burn_arguments(arguments)
        
        # Extract transaction details
        transaction = call.get('Transaction', {})
        block = call.get('Block', {})
        
        # Get token info
        token0_address = params.get('token0')
        token1_address = params.get('token1')
        
        # Skip events that don't have proper token data (common with burn events)
        if not token0_address or not token1_address:
            if i < 5:
                print(f"Skipping event {i+1} - missing token addresses")
            continue
        
        token0_info = token_decimals.get(token0_address, {})
        token1_info = token_decimals.get(token1_address, {})
        
        token0_symbol = token0_info.get('symbol', 'Unknown')
        token1_symbol = token1_info.get('symbol', 'Unknown')
        token0_decimals = token0_info.get('decimals', 18)
        token1_decimals = token1_info.get('decimals', 18)
        
        # Convert amounts
        amount0_desired = convert_amount(params.get('amount0Desired', '0'), token0_decimals)
        amount1_desired = convert_amount(params.get('amount1Desired', '0'), token1_decimals)
        
        # Calculate price bands from ticks
        tick_lower = params.get('tickLower')
        tick_upper = params.get('tickUpper')
        price_lower = None
        price_upper = None
        
        if tick_lower is not None and tick_upper is not None:
            price_lower = calculate_price_from_tick(tick_lower, token0_decimals, token1_decimals)
            price_upper = calculate_price_from_tick(tick_upper, token0_decimals, token1_decimals)
        
        event_data = {
            'event_type': event_type,
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
            'amounts': {
                'amount0_desired': amount0_desired,
                'amount1_desired': amount1_desired,
                'amount0_min': convert_amount(params.get('amount0Min', '0'), token0_decimals),
                'amount1_min': convert_amount(params.get('amount1Min', '0'), token1_decimals)
            },
            'fee': params.get('fee'),
            'ticks': {
                'lower': tick_lower,
                'upper': tick_upper
            },
            'price_band': {
                'lower': price_lower,
                'upper': price_upper
            },
            'recipient': params.get('recipient'),
            'deadline': params.get('deadline'),
            'transaction': {
                'hash': transaction.get('Hash'),
                'from': transaction.get('From'),
                'to': transaction.get('To'),
                'value_in_usd': transaction.get('ValueInUSD'),
                'time': transaction.get('Time')
            },
            'block': {
                'number': block.get('Number'),
                'time': block.get('Time')
            }
        }
        
        processed_events.append(event_data)
        
        # Only show detailed output for first 5 events
        if i < 5:
            print(f"Event Type: {event_type}")
            print(f"Token0: {token0_symbol} ({token0_address}) - Amount: {amount0_desired:.6f}")
            print(f"Token1: {token1_symbol} ({token1_address}) - Amount: {amount1_desired:.6f}")
            print(f"Fee: {params.get('fee')}")
            print(f"Tick Range: {tick_lower} to {tick_upper}")
            if price_lower is not None and price_upper is not None:
                print(f"Price Band: {price_lower:.6f} to {price_upper:.6f} {token1_symbol} per {token0_symbol}")
            print(f"Recipient: {params.get('recipient')}")
            print(f"Transaction: {transaction.get('Hash')}")
    
    return processed_events


def save_processed_mint_events_to_file(processed_events: list, filename: str = "processed_mint_events.json") -> str:
    """Save processed mint events to a JSON file"""
    # Create output directory if it doesn't exist
    output_dir = "bitquery_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    full_filename = f"{filename}"
    filepath = os.path.join(output_dir, full_filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(processed_events, f, indent=2)
    
    print(f"\n💾 Saved {len(processed_events)} processed mint events to: {filepath}")
    return filepath


def main(include_realtime=True):
    """Main function"""
    print("Starting mint events processing (historical + real-time)...")
    
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
        
        # Process both historical and real-time mint events
        processed_events = process_mint_events_with_decimals(client, start_date_str, end_date_str, include_realtime)
        
        if processed_events:
            # Save processed events to file
            filepath = save_processed_mint_events_to_file(processed_events)
            print(f"\n✅ Successfully processed {len(processed_events)} mint events!")
            print(f"📁 Results saved to: {filepath}")
        else:
            print("\n❌ No mint events were processed!")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
