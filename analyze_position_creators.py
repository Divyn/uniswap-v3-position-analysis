"""
Analyze position creators and find top creators by activity and volume
"""
import json
import os
from collections import defaultdict
from datetime import datetime
from bitquery_client import BitqueryClient


def extract_position_creators_from_response(data: dict) -> list:
    """Extract position creators from mint events response"""
    creators_data = []
    
    calls = data.get('data', {}).get('EVM', {}).get('Calls', [])
    
    for call in calls:
        transaction = call.get('Transaction', {})
        block = call.get('Block', {})
        returns = call.get('Returns', [])
        
        # Extract position creator (transaction sender)
        creator_address = transaction.get('From')
        if not creator_address:
            continue
            
        # Extract position details from returns
        token_id = None
        liquidity = None
        amount0 = None
        amount1 = None
        
        for return_item in returns:
            name = return_item.get('Name', '')
            value = return_item.get('Value', {})
            
            if name == 'tokenId' and 'bigInteger' in value:
                token_id = value['bigInteger']
            elif name == 'liquidity' and 'bigInteger' in value:
                liquidity = value['bigInteger']
            elif name == 'amount0' and 'bigInteger' in value:
                amount0 = value['bigInteger']
            elif name == 'amount1' and 'bigInteger' in value:
                amount1 = value['bigInteger']
        
        # Extract token addresses from arguments
        arguments = call.get('Arguments', [])
        token0_address = None
        token1_address = None
        fee = None
        tick_lower = None
        tick_upper = None
        
        for arg in arguments:
            index = arg.get('Index', -1)
            value = arg.get('Value', {})
            
            if index == 0 and 'address' in value:
                token0_address = value['address']
            elif index == 1 and 'address' in value:
                token1_address = value['address']
            elif index == 2 and 'bigInteger' in value:
                fee = value['bigInteger']
            elif index == 3 and 'bigInteger' in value:
                tick_lower = int(value['bigInteger'])
            elif index == 4 and 'bigInteger' in value:
                tick_upper = int(value['bigInteger'])
        
        creator_data = {
            'creator_address': creator_address,
            'token_id': token_id,
            'token0_address': token0_address,
            'token1_address': token1_address,
            'fee': fee,
            'tick_lower': tick_lower,
            'tick_upper': tick_upper,
            'liquidity': liquidity,
            'amount0': amount0,
            'amount1': amount1,
            'transaction_hash': transaction.get('Hash'),
            'transaction_value_usd': transaction.get('ValueInUSD'),
            'block_number': block.get('Number'),
            'timestamp': block.get('Time')
        }
        
        creators_data.append(creator_data)
    
    return creators_data


def analyze_top_creators(creators_data: list) -> dict:
    """Analyze and rank position creators by various metrics"""
    
    # Group by creator address
    creator_stats = defaultdict(lambda: {
        'total_positions': 0,
        'total_liquidity': 0,
        'total_usd_value': 0,
        'unique_pairs': set(),
        'fee_tiers': defaultdict(int),
        'positions': [],
        'first_position_time': None,
        'last_position_time': None
    })
    
    for creator_data in creators_data:
        creator_address = creator_data['creator_address']
        stats = creator_stats[creator_address]
        
        # Update counters
        stats['total_positions'] += 1
        
        # Handle liquidity safely
        liquidity = creator_data.get('liquidity')
        if liquidity:
            try:
                stats['total_liquidity'] += int(liquidity)
            except (ValueError, TypeError):
                pass
        
        # Update USD value
        usd_value = creator_data.get('transaction_value_usd')
        if usd_value:
            try:
                stats['total_usd_value'] += float(usd_value)
            except (ValueError, TypeError):
                pass
        
        # Track unique pairs
        if creator_data.get('token0_address') and creator_data.get('token1_address'):
            pair = f"{creator_data['token0_address']}/{creator_data['token1_address']}"
            stats['unique_pairs'].add(pair)
        
        # Track fee tiers
        if creator_data.get('fee'):
            stats['fee_tiers'][creator_data['fee']] += 1
        
        # Track position details
        stats['positions'].append(creator_data)
        
        # Track time range
        timestamp = creator_data.get('timestamp')
        if timestamp:
            if not stats['first_position_time'] or timestamp < stats['first_position_time']:
                stats['first_position_time'] = timestamp
            if not stats['last_position_time'] or timestamp > stats['last_position_time']:
                stats['last_position_time'] = timestamp
    
    # Convert sets to counts and prepare for ranking
    for creator_address, stats in creator_stats.items():
        stats['unique_pairs_count'] = len(stats['unique_pairs'])
        stats['unique_pairs'] = list(stats['unique_pairs'])  # Convert set to list for JSON serialization
    
    return dict(creator_stats)


def rank_creators(creator_stats: dict, top_n: int = 20) -> dict:
    """Rank creators by different metrics"""
    
    creators_list = list(creator_stats.items())
    
    # Sort by different metrics
    by_positions = sorted(creators_list, key=lambda x: x[1]['total_positions'], reverse=True)[:top_n]
    by_liquidity = sorted(creators_list, key=lambda x: x[1]['total_liquidity'], reverse=True)[:top_n]
    by_usd_value = sorted(creators_list, key=lambda x: x[1]['total_usd_value'], reverse=True)[:top_n]
    by_unique_pairs = sorted(creators_list, key=lambda x: x[1]['unique_pairs_count'], reverse=True)[:top_n]
    
    rankings = {
        'by_positions': by_positions,
        'by_liquidity': by_liquidity,
        'by_usd_value': by_usd_value,
        'by_unique_pairs': by_unique_pairs
    }
    
    return rankings


def print_top_creators(rankings: dict):
    """Print top creators in a formatted way"""
    
    print("=" * 80)
    print("TOP POSITION CREATORS ANALYSIS")
    print("=" * 80)
    
    # Top by number of positions
    print(f"\n🏆 TOP 10 BY NUMBER OF POSITIONS:")
    print("-" * 60)
    for i, (creator, stats) in enumerate(rankings['by_positions'][:10], 1):
        print(f"{i:2d}. {creator}")
        print(f"    Positions: {stats['total_positions']}")
        print(f"    Total Liquidity: {stats['total_liquidity']:,}")
        print(f"    USD Value: ${stats['total_usd_value']:,.2f}")
        print(f"    Unique Pairs: {stats['unique_pairs_count']}")
        print(f"    Time Range: {stats['first_position_time']} to {stats['last_position_time']}")
        print()
    
    # Top by USD value
    print(f"\n💰 TOP 10 BY USD VALUE:")
    print("-" * 60)
    for i, (creator, stats) in enumerate(rankings['by_usd_value'][:10], 1):
        print(f"{i:2d}. {creator}")
        print(f"    USD Value: ${stats['total_usd_value']:,.2f}")
        print(f"    Positions: {stats['total_positions']}")
        print(f"    Total Liquidity: {stats['total_liquidity']:,}")
        print(f"    Unique Pairs: {stats['unique_pairs_count']}")
        print()
    
    # Top by liquidity
    print(f"\n💧 TOP 10 BY TOTAL LIQUIDITY:")
    print("-" * 60)
    for i, (creator, stats) in enumerate(rankings['by_liquidity'][:10], 1):
        print(f"{i:2d}. {creator}")
        print(f"    Total Liquidity: {stats['total_liquidity']:,}")
        print(f"    Positions: {stats['total_positions']}")
        print(f"    USD Value: ${stats['total_usd_value']:,.2f}")
        print(f"    Unique Pairs: {stats['unique_pairs_count']}")
        print()
    
    # Top by unique pairs
    print(f"\n🔄 TOP 10 BY UNIQUE PAIRS:")
    print("-" * 60)
    for i, (creator, stats) in enumerate(rankings['by_unique_pairs'][:10], 1):
        print(f"{i:2d}. {creator}")
        print(f"    Unique Pairs: {stats['unique_pairs_count']}")
        print(f"    Positions: {stats['total_positions']}")
        print(f"    USD Value: ${stats['total_usd_value']:,.2f}")
        print(f"    Total Liquidity: {stats['total_liquidity']:,}")
        print()


def save_creator_analysis(creator_stats: dict, rankings: dict, filename: str = "creator_analysis.json") -> str:
    """Save creator analysis to JSON file"""
    output_dir = "bitquery_responses"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    
    analysis_data = {
        'summary': {
            'total_creators': len(creator_stats),
            'analysis_timestamp': datetime.now().isoformat(),
            'total_positions': sum(stats['total_positions'] for stats in creator_stats.values())
        },
        'creator_stats': creator_stats,
        'rankings': rankings
    }
    
    with open(filepath, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"\n💾 Saved creator analysis to: {filepath}")
    return filepath


def main():
    """Main function to analyze position creators"""
    print("🔍 Analyzing position creators...")
    
    # Initialize BitQuery client
    client = BitqueryClient()
    
    try:
        # Get recent position creators
        print("Fetching recent mint events...")
        response = client.get_recent_position_creators(limit=20000)
        
        if not response.get('data', {}).get('EVM', {}).get('Calls'):
            print("❌ No mint events found!")
            return
        
        # Extract creator data
        print("Processing creator data...")
        creators_data = extract_position_creators_from_response(response)
        print(f"Found {len(creators_data)} position creation events")
        
        if not creators_data:
            print("❌ No creator data extracted!")
            return
        
        # Analyze creators
        print("Analyzing creator statistics...")
        creator_stats = analyze_top_creators(creators_data)
        print(f"Found {len(creator_stats)} unique creators")
        
        # Rank creators
        rankings = rank_creators(creator_stats, top_n=20)
        
        # Print results
        print_top_creators(rankings)
        
        # Save analysis
        filepath = save_creator_analysis(creator_stats, rankings)
        
        print(f"\n✅ Analysis complete! Results saved to: {filepath}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
