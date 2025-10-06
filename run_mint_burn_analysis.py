#!/usr/bin/env python3
"""
Script to run mint/burn analysis and open the visualization
"""
import subprocess
import webbrowser
import os
import time
from pathlib import Path

def run_mint_processing():
    """Run the mint processing script"""
    print("🚀 Starting mint events processing...")
    
    try:
        # Import and run the main function
        from process_mint_burn import main
        main(include_realtime=True)
        
        print("✅ Mint processing completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during mint processing: {e}")
        return False

def open_visualization():
    """Open the mint events visualization in browser"""
    chart_path = Path("mint_burn_chart.html").resolve()
    
    if chart_path.exists():
        print(f"🌐 Opening visualization: {chart_path}")
        webbrowser.open(f"file://{chart_path}")
    else:
        print("❌ Chart file not found. Please check if mint_burn_chart.html exists.")

def start_local_server():
    """Start a simple HTTP server to serve the chart"""
    try:
        import http.server
        import socketserver
        import threading
        
        PORT = 8001
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=os.getcwd(), **kwargs)
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 Starting local server at http://localhost:{PORT}")
            print(f"📊 Open http://localhost:{PORT}/mint_burn_chart.html to view the chart")
            print("Press Ctrl+C to stop the server")
            
            # Open browser
            webbrowser.open(f"http://localhost:{PORT}/mint_burn_chart.html")
            
            # Start server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🔍 Uniswap V3 Mint Events Analyzer")
    print("=" * 60)
    
    # Step 1: Run mint processing
    success = run_mint_processing()
    
    if success:
        # Step 2: Start local server and open visualization
        print("\n" + "=" * 60)
        print("📊 Opening Visualization")
        print("=" * 60)
        start_local_server()
    else:
        print("\n❌ Cannot proceed to visualization due to processing errors.")
        print("Please fix the errors and try again.")

if __name__ == "__main__":
    main()
