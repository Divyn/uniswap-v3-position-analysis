"""
Streamlined main script for Uniswap V3 position tracking
"""
import sys
from process_positions import main as positions_main
from process_mint_burn import main as mint_burn_main
from analyze_position_creators import main as creators_main

def show_help():
    print("Uniswap V3 Liquidity Position Tracker")
    print("Usage:")
    print("  python main.py positions    - Run position tracking (default)")
    print("  python main.py mint         - Run mint events analysis (liquidity additions)")
    print("  python main.py creators     - Analyze top position creators")
    print("  python main.py help         - Show this help")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "positions":
            print("🔍 Running position tracking...")
            positions_main(include_realtime=True)
        elif command == "mint":
            print("🔥 Running mint events analysis...")
            mint_burn_main(include_realtime=True)
        elif command == "creators":
            print("👥 Analyzing top position creators...")
            creators_main()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
    else:
        # Default: run position processing
        print("🔍 Running position tracking (default)...")
        positions_main(include_realtime=True)
