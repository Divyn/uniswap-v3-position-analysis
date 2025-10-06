"""
Configuration settings for the Uniswap V3 Liquidity Position Tracker
"""
import os
from dotenv import load_dotenv

load_dotenv()

# BitQuery Configuration
BITQUERY_OAUTH_TOKEN = "ory_"
BITQUERY_STREAMING_ENDPOINT = "https://streaming.bitquery.io/graphql"

# Uniswap V3 Configuration
UNISWAP_V3_FACTORY = '0x1F98431c8aD98523631AE4a59f267346ea31F984'
UNISWAP_V3_POSITION_MANAGER = '0xC36442b4a4522E871399CD717aBDD847Ab11FE88'

# Token Addresses
WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
USDT_ADDRESS = '0xdAC17F958D2ee523a2206206994597C13D831ec7'

# WETH/USDT Pool Configuration
WETH_USDT_POOL_ADDRESS = '0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36'  # 0.3% fee tier
WETH_USDT_FEE_TIER = 3000  # 0.3%

# Analysis Configuration
DEFAULT_START_BLOCK = 12300000  # Approximate start of Uniswap V3
DEFAULT_END_BLOCK = None  # Current block
BATCH_SIZE = 1000  # Number of transactions to process per batch
