# Fetches active trade offers from Path of Exile's public stash API
# and stores them in a SQLite database.
import sqlite3
import requests
import json
import time
import sys
import os
import logging
import argparse
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the trade API to fetch active trade offers
TRADE_API_URL = 'https://www.pathofexile.com/api/trade2/search/poe2/Standard'
TRADE_OFFER_URL = 'https://www.pathofexile.com/api/trade2/fetch/{}'
TRADE_STASH_URL = 'https://www.pathofexile.com/api/trade2/fetch/{}?query={}'
TRADE_LEAGUE = 'Standard'

# Construct trade query for 2 hand mauls
TRADE_QUERY = {
    "query": {
        "status": {
            "option": "online"
        },
        "stats": [
            {
                "type": "and",
                "filters": [],
                "disabled": "false"
            }
        ]
    },
    "sort": {
        "price": "asc"
    }
}

def headers(session):
    return {
        'Cookie': f'POESESSID={session}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

# Fetch and iterate over all trade offers
def fetch_trade_offers(session, query: Dict) -> List[str]:
    # Fetch trade offers from the trade API, ignore SSL certificate errors
    response = requests.post(TRADE_API_URL, headers=headers(session), json=query, verify=False)
    response.raise_for_status()
    trade_offers = response.json()

    # Extract the list of trade IDs
    trade_ids = trade_offers['result']

    # Return the list of trade IDs
    return trade_ids

# Allow POESESSIONID to be passed as an argument
def main():
    # Parse command line arguments, allow to set session id
    parser = argparse.ArgumentParser(description='Fetches active trade offers from Path of Exile\'s public stash API and stores them in a SQLite database.')
    parser.add_argument('-s', '--session', help='POESESSID cookie value to use for fetching trade offers.')
    args = parser.parse_args()

    # Fetch trade offers
    session = args.session
    if session is None:
        logger.error('No POESESSID cookie value provided.')
        sys.exit(1)

    # Fetch trade offers
    trade_ids = fetch_trade_offers(session, TRADE_QUERY)
    for trade_id in trade_ids:
        # Fetch the trade offer
        response = requests.get(TRADE_OFFER_URL.format(trade_id), headers=headers(session), verify=False)
        response.raise_for_status()
        trade_offer = response.json()

        # Print the trade offer
        print(json.dumps(trade_offer, indent=2))
    
if __name__ == '__main__':
    main()
    