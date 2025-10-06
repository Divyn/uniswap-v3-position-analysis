"""
Bitquery client for fetching Uniswap V3 liquidity position data
"""
import requests
from typing import Dict


from config import BITQUERY_OAUTH_TOKEN, BITQUERY_STREAMING_ENDPOINT


class BitqueryClient:
    """Client for interacting with Bitquery GraphQL API"""

    def __init__(self):
        self.endpoint = BITQUERY_STREAMING_ENDPOINT
        self.headers = {
            'Authorization': f'Bearer {BITQUERY_OAUTH_TOKEN}',
            'Content-Type': 'application/json'
        }

    def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query against Bitquery"""
        payload = {
            'query': query,
            'variables': variables or {}
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error executing Bitquery request: {e}")
            return {}


    def get_historical_positions(self, start_date: str, end_date: str) -> Dict:
        query = """
        query RecentPositions($startDate: String!, $endDate: String!) {
          EVM(dataset: archive, network: eth) {
            Calls(
              where: {
                Call: {
                  Signature: { Name: {is: "positions"} }
                  To: {is: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"}
                }
                Block: { Date: { after: $startDate before: $endDate } }
              }
              limit: {count: 2000}
              orderBy: {descending: Block_Number}
            ) {
              Arguments {
                Index
                Name
                Type
                Path {
                  Name
                  Index
                }
                Value {
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
              }
              Call {
                Signature {
                  Name
                }
                To
                Value
                ValueInUSD
                From
              }
              Transaction {
                From
                To
                Hash
                ValueInUSD
                Value
                Time
              }
              Block {
                Number
                Time
              }
              Returns {
                Value {
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
                Type
                Name
              }
            }
          }
        }
        """
        return self.execute_query(query, {"startDate": start_date, "endDate": end_date})

    def get_recent_positions_realtime(self) -> Dict:
        """Get very recent positions from realtime database (no date filter)"""
        query = """
        query RecentPositionsRealtime {
          EVM(network: eth) {
            Calls(
              where: {
                Call: {
                  Signature: { Name: {is: "positions"} }
                  To: {is: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"}
                }
              }
              limit: {count: 20000}
              orderBy: {descending: Block_Number}
            ) {
              Arguments {
                Index
                Name
                Type
                Path {
                  Name
                  Index
                }
                Value {
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
              }
              Call {
                Signature {
                  Name
                }
                To
                Value
                ValueInUSD
                From
              }
              Transaction {
                From
                To
                Hash
                ValueInUSD
                Value
                Time
              }
              Block {
                Number
                Time
              }
              Returns {
                Value {
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
                Type
                Name
              }
            }
          }
        }
        """
        return self.execute_query(query)



    def get_token_decimals(self, token_addresses: list) -> Dict:
        """Query token decimals for the given addresses"""
        token_list = '", "'.join(token_addresses)
        
        query = f"""
        query TokenDecimals {{
          EVM(network: eth, dataset: archive) {{
            Transfers(
              where: {{
                Transfer: {{Currency: {{SmartContract: {{in: ["{token_list}"]}}}}}}
                Block: {{Date: {{before: "2025-09-22", after: "2025-09-01"}}}}
              }}
              limitBy: {{by: Transfer_Currency_SmartContract, count: 1}}
              limit: {{count: 1000}}
              orderBy: {{descending: Block_Number}}
            ) {{
              Transfer {{
                Currency {{
                  Decimals
                  Symbol
                  SmartContract
                  Name
                }}
              }}
            }}
          }}
        }}
        """
        return self.execute_query(query)

    def get_historical_mint_events(self, start_date: str, end_date: str, limit: int = 2000) -> Dict:
        """Get historical mint events for Uniswap V3 positions"""
        query = """
        query HistoricalMintEvents($startDate: String!, $endDate: String!, $limit: Int!) {
          EVM(dataset: archive, network: eth) {
            Calls(
              where: {
                Call: {
                  Signature: { Name: { is: "mint" } }
                  To: { is: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88" }
                }
                Block: { Date: { after: $startDate, before: $endDate } }
              }
              limit: { count: $limit }
              orderBy: { descending: Block_Number }
            ) {
              Arguments {
                Index
                Name
                Type
                Path {
                  Name
                  Index
                }
                Value {
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
              }
              Call {
                Signature {
                  Name
                }
                To
                Value
                ValueInUSD
                From
              }
              Transaction {
                From
                To
                Hash
                ValueInUSD
                Value
                Time
              }
              Block {
                Number
                Time
              }
            }
          }
        }
        """
        return self.execute_query(query, {
            "startDate": start_date,
            "endDate": end_date,
            "limit": limit
        })

    def get_recent_mint_events_realtime(self, limit: int = 2000) -> Dict:
        """Get recent mint events from realtime database"""
        query = """
        query RecentMintEventsRealtime($limit: Int!) {
          EVM(network: eth) {
            Calls(
              where: {
                Call: {
                  Signature: { Name: { is: "mint" } }
                  To: { is: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88" }
                }
              }
              limit: { count: $limit }
              orderBy: { descending: Block_Number }
            ) {
              Arguments {
                Index
                Name
                Type
                Path {
                  Name
                  Index
                }
                Value {
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
              }
              Call {
                Signature {
                  Name
                }
                To
                Value
                ValueInUSD
                From
              }
              Transaction {
                From
                To
                Hash
                ValueInUSD
                Value
                Time
              }
              Block {
                Number
                Time
              }
            }
          }
        }
        """
        return self.execute_query(query, {"limit": limit})

    def get_recent_position_creators(self, limit: int = 20000) -> Dict:
        """Get recent position creators from mint events"""
        query = """
        query RecentPositionsRealtime($limit: Int!) {
          EVM(network: eth) {
            Calls(
              where: {
                Call: {
                  Signature: { Name: { is: "mint" } }
                  To: { is: "0xC36442b4a4522E871399CD717aBDD847Ab11FE88" }
                }
              }
              limit: { count: $limit }
              orderBy: { descending: Block_Number }
            ) {
              Arguments {
                Index
                Name
                Type
                Path {
                  Name
                  Index
                }
                Value {
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
              }
              Call {
                Signature {
                  Name
                }
                To
                Value
                ValueInUSD
                From
              }
              Transaction {
                From
                To
                Hash
                ValueInUSD
                Value
                Time
              }
              Block {
                Number
                Time
              }
              Returns {
                Value {
                  ... on EVM_ABI_Boolean_Value_Arg {
                    bool
                  }
                  ... on EVM_ABI_Bytes_Value_Arg {
                    hex
                  }
                  ... on EVM_ABI_BigInt_Value_Arg {
                    bigInteger
                  }
                  ... on EVM_ABI_Address_Value_Arg {
                    address
                  }
                  ... on EVM_ABI_String_Value_Arg {
                    string
                  }
                  ... on EVM_ABI_Integer_Value_Arg {
                    integer
                  }
                }
                Type
                Name
              }
            }
          }
        }
        """
        return self.execute_query(query, {"limit": limit})
