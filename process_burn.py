"""
Process Uniswap V3 burn events to analyze position closure patterns
"""
import json
import os
from datetime import datetime, timedelta
from bitquery_client import BitQueryClient


def parse_burn_arguments(arguments: list) -> dict:
    """Parse burn function arguments to extract tokenId"""
    params = {}
    
    for arg in arguments:
        name = arg.get('Name', '')
        value = arg.get('Value', {})
        
        # Burn events only have tokenId as argument
        if name == 'tokenId' and 'bigInteger' in value:
            params['tokenId'] = value['bigInteger']
    
    return params


def process_burn_events(client: BitQueryClient, start_date: str = None, end_date: str = None, include_realtime: bool = True):
    """Main function to fetch and process burn events"""
    all_events = []
    
    # Step 1: Get historical burn events
    print("Fetching historical burn events...")
    historical_response = client.get_historical_burn_events(start_date, end_date)
    
    if historical_response.get('data', {}).get('EVM', {}).get('Calls'):
        historical_calls = historical_response.get('data', {}).get('EVM', {}).get('Calls', [])
        all_events.extend(historical_calls)
        print(f"Found {len(historical_calls)} historical burn events")
    
    # Step 2: Get real-time burn events (if requested)
    if include_realtime:
        print("Fetching real-time burn events...")
        realtime_response = client.get_recent_burn_events_realtime()
        
        if realtime_response.get('data', {}).get('EVM', {}).get('Calls'):
            realtime_calls = realtime_response.get('data', {}).get('EVM', {}).get('Calls', [])
            all_events.extend(realtime_calls)
            print(f"Found {len(realtime_calls)} real-time burn events")
    
    print(f"Total burn events to process: {len(all_events)}")
    
    if not all_events:
        print("No burn event data found!")
        return []
    
    # Create a combined response structure
    events_response = {
        'data': {
            'EVM': {
                'Calls': all_events
            }
        }
    }
    
    # DEBUG: Let's see what's actually in the response
    print("\n=== DEBUG: First burn event data ===")
    first_call = events_response.get('data', {}).get('EVM', {}).get('Calls', [])[0]
    print("Arguments:", json.dumps(first_call.get('Arguments', []), indent=2))
    print("Call Signature:", first_call.get('Call', {}).get('Signature', {}).get('Name'))
    print("===================================\n")
    
    # Process burn events
    print("\nProcessing burn events...")
    calls = events_response.get('data', {}).get('EVM', {}).get('Calls', [])
    
    processed_events = []
    
    for i, call in enumerate(calls):
        if i < 5:  # Only show detailed output for first 5 events
            print(f"\n--- Burn Event {i+1} ---")
        elif i == 5:
            print(f"\n... Processing remaining {len(calls) - 5} events silently ...")
        
        # Extract event type (should be 'burn' for all events)
        event_type = call.get('Call', {}).get('Signature', {}).get('Name', 'burn')
        
        # Parse arguments to get tokenId
        arguments = call.get('Arguments', [])
        params = parse_burn_arguments(arguments)
        
        # Extract transaction details
        transaction = call.get('Transaction', {})
        block = call.get('Block', {})
        
        # Get tokenId
        token_id = params.get('tokenId')
        
        if not token_id:
            if i < 5:
                print(f"Skipping event {i+1} - missing tokenId")
            continue
        
        event_data = {
            'event_type': event_type,
            'tokenId': token_id,
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
            print(f"Token ID (NFT Position): {token_id}")
            print(f"Transaction From: {transaction.get('From')}")
            print(f"Transaction: {transaction.get('Hash')}")
            print(f"Block Time: {block.get('Time')}")
    
    return processed_events


def save_processed_burn_events_to_file(processed_events: list, filename: str = "processed_burn_events.json") -> str:
    """Save processed burn events to a JSON file"""
    # Create output directory if it doesn't exist
    output_dir = "bitquery_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename
    full_filename = f"{filename}"
    filepath = os.path.join(output_dir, full_filename)
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(processed_events, f, indent=2)
    
    print(f"\n💾 Saved {len(processed_events)} processed burn events to: {filepath}")
    return filepath


def analyze_burn_patterns(processed_events: list) -> dict:
    """Analyze burn event patterns"""
    print("\n=== BURN EVENT ANALYSIS ===")
    
    # Time-based analysis
    events_by_hour = {}
    events_by_day = {}
    unique_burners = set()
    
    for event in processed_events:
        timestamp = event['block']['time']
        burner = event['transaction']['from']
        
        unique_burners.add(burner)
        
        # Parse timestamp
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        hour = dt.strftime('%Y-%m-%d %H:00')
        day = dt.strftime('%Y-%m-%d')
        
        events_by_hour[hour] = events_by_hour.get(hour, 0) + 1
        events_by_day[day] = events_by_day.get(day, 0) + 1
    
    # Find peak activity
    peak_hour = max(events_by_hour.items(), key=lambda x: x[1]) if events_by_hour else (None, 0)
    peak_day = max(events_by_day.items(), key=lambda x: x[1]) if events_by_day else (None, 0)
    
    analysis = {
        'total_burns': len(processed_events),
        'unique_burners': len(unique_burners),
        'avg_burns_per_burner': len(processed_events) / len(unique_burners) if unique_burners else 0,
        'peak_hour': {'time': peak_hour[0], 'count': peak_hour[1]},
        'peak_day': {'date': peak_day[0], 'count': peak_day[1]},
        'events_by_day': events_by_day,
        'events_by_hour': events_by_hour
    }
    
    print(f"\n📊 Total Burn Events: {analysis['total_burns']}")
    print(f"👥 Unique Burners: {analysis['unique_burners']}")
    print(f"📈 Avg Burns per Burner: {analysis['avg_burns_per_burner']:.2f}")
    print(f"⏰ Peak Hour: {peak_hour[0]} ({peak_hour[1]} burns)")
    print(f"📅 Peak Day: {peak_day[0]} ({peak_day[1]} burns)")
    
    return analysis


def main(include_realtime=True):
    """Main function"""
    print("Starting burn events processing (historical + real-time)...")
    
    # Initialize Bitquery client
    client = BitQueryClient()
    
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
        
        # Process both historical and real-time burn events
        processed_events = process_burn_events(client, start_date_str, end_date_str, include_realtime)
        
        if processed_events:
            # Analyze patterns
            analysis = analyze_burn_patterns(processed_events)
            
            # Save processed events to file
            filepath = save_processed_burn_events_to_file(processed_events)
            print(f"\n✅ Successfully processed {len(processed_events)} burn events!")
            print(f"📁 Results saved to: {filepath}")
            
            # Save analysis to separate file
            analysis_filepath = os.path.join("bitquery_responses", "burn_analysis.json")
            with open(analysis_filepath, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            print(f"📊 Analysis saved to: {analysis_filepath}")
        else:
            print("\n❌ No burn events were processed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

