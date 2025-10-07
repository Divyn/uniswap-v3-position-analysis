"""
Runner script to execute burn event analysis
"""
from process_burn import main

if __name__ == "__main__":
    print("=" * 80)
    print("UNISWAP V3 BURN EVENT ANALYSIS")
    print("=" * 80)
    print()
    
    # Run the analysis (includes both historical and realtime data)
    main(include_realtime=True)
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print()
    print("📊 View the interactive burn chart: open burn_chart.html in your browser")
    print()

