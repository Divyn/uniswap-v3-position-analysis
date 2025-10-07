# Uniswap V3 Liquidity Position Tracker

A streamlined tool for tracking Uniswap V3 liquidity positions and extracting token decimals.

## Files Overview

- **`main.py`** - Main entry point for position tracking and mint/burn analysis
- **`process_positions.py`** - Core position processing logic with token decimals integration
- **`process_mint_burn.py`** - Mint/burn events processing logic with liquidity event analysis
- **`extract_token_decimals.py`** - Standalone script for extracting token decimals from position data
- **`bitquery_client.py`** - BitQuery API client for fetching position, mint/burn, and token data
- **`config.py`** - Configuration settings and API credentials
- **`positions_chart.html`** - HTML visualization of position data
- **`mint_burn_chart.html`** - HTML visualization of mint/burn events
- **`creator_analysis_chart.html`** - HTML visualization of position creators analysis
- **`run_mint_burn_analysis.py`** - Convenience script to run mint/burn analysis and open visualization

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your BitQuery API token in `config.py` file:**
   ```
   BITQUERY_OAUTH_TOKEN=your_token_here
   ```

3. **Run position tracking:**
   ```bash
   python3 main.py positions
   ```

4. **Run mint events analysis:**
   ```bash
   python3 main.py mint
   ```

5. **Analyze top position creators:**
   ```bash
   python3 main.py creators
   ```

6. **Extract token decimals (optional):**
   ```bash
   python extract_token_decimals.py
   ```

7. **Analyse burn events**
```
python3 main.py burn

```

7. **View visualizations:**
   - **Positions**: Open `positions_chart.html` in browser
   - **Mint Events**: Open `mint_burn_chart.html` in browser
   - **Creator Analysis**: Open `creator_analysis_chart.html` in browser
   - **Quick start**: Run `python3 run_mint_burn_analysis.py` for mint analysis with auto-opened visualization

## What Each Script Does

### `main.py`
- Fetches historical and real-time Uniswap V3 position data
- Processes positions with token decimals
- Saves processed data to `bitquery_responses/processed_positions.json`

### `extract_token_decimals.py`
- Reads position data from previous runs
- Extracts unique token addresses
- Queries token decimals from BitQuery
- Creates lookup tables for token metadata

### `process_positions.py`
- Contains the core logic for processing position data
- Converts raw blockchain amounts to human-readable values
- Calculates price bands from tick data
- Handles both historical and real-time data

### `process_mint_burn.py`
- Processes mint events (liquidity additions) - burn events require tokenId mapping (planned for future)
- Extracts token addresses, amounts, and price bands from mint parameters
- Calculates converted amounts using token decimals
- Provides insights into liquidity provider behavior and deployment strategies

### `analyze_position_creators.py`
- Analyzes recent position creators from mint events
- Identifies top creators by number of positions, USD value, and total liquidity
- Provides insights into liquidity provider behavior patterns
- Ranks creators by various metrics including unique trading pairs

## Output Files

- `bitquery_responses/processed_positions.json` - Processed position data
- `bitquery_responses/processed_mint_events.json` - Processed mint events data
- `bitquery_responses/creator_analysis.json` - Top position creators analysis
- `bitquery_responses/token_decimals.json` - Token decimals data
- `bitquery_responses/token_decimals_lookup_*.json` - Token metadata lookup

## Configuration

Edit `config.py` to modify:
- Date ranges for queries
- Token addresses
- Pool configurations
- API endpoints

```

python3 -m http.server 8000

```
