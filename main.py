# Fetches active trade offers from Path of Exile's public stash API
# and stores them in a SQLite database.
import requests
import json
import time
import re
import logging
import argparse
from typing import Dict, List
# import jsonify 



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
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    if session:
        headers['Cookie'] = f'POESESSID={session}'
    return headers

def get_session_cookie(existing, request):
    return request.cookies.get('POESESSID') if request.cookies.get('POESESSID') else existing

def parse_rate_limit_header(header_value):
    """
    Generalized function to parse a rate-limit header into structured rules.
    """
    rules = []
    # Match any number of rules in the format "value1:value2:value3"
    pattern = r'(\d+):(\d+):(\d+)'
    matches = re.findall(pattern, header_value)
    for match in matches:
        # Convert matched values to integers
        values = list(map(int, match))
        rules.append({
            "requests": values[0], 
            "window_seconds": values[1], 
            "penalty_seconds": values[2]
        })
    return rules

def parse_rate_headers(request):
    # Extract headers
    rate_limit_ip = request.headers.get('x-rate-limit-ip')
    rate_limit_ip_state = request.headers.get('x-rate-limit-ip-state')
    
    # Parse headers if they are present
    rate_limit_rules = parse_rate_limit_header(rate_limit_ip) if rate_limit_ip else None
    rate_limit_state = parse_rate_limit_header(rate_limit_ip_state) if rate_limit_ip_state else None

    return rate_limit_rules, rate_limit_state

def wait_until_can_make_request(previous_response):
    """
    Determine if a request can be made based on rate-limiting rules and state.
    :param rules: List of rate-limiting rules (parsed from x-rate-limit-ip).
    :param state: List of current state (parsed from x-rate-limit-ip-state).
    :return: True if a request can be made, False otherwise.
    """
    rules, state = parse_rate_headers(previous_response)
    for rule, current in zip(rules, state):
        # Check if penalty is still in effect
        if current['penalty_seconds']:
            # Wait until penalty is over
            time.sleep(rule['penalty_seconds'] - current['penalty_seconds'])

        # Check if requests exceed the limit
        if current['requests'] >= rule['requests'] and current['window_seconds'] <= rule['window_seconds']:
            # Wait until window is over plus one second
            time.sleep(rule['window_seconds'] - current['window_seconds'] + 1)

    # If all rules are satisfied, request can be made
    pass

# Fetch and iterate over all trade offers
def fetch_trade_offers(session, query: Dict) -> List[str]:
    # Fetch trade offers from the trade API, ignore SSL certificate errors
    response = requests.post(TRADE_API_URL, headers=headers(session), json=query, verify=False)
    response.raise_for_status()
    trade_offers = response.json()

    # Extract the list of trade IDs
    trade_ids = trade_offers['result']

    # Return the list of trade IDs
    return trade_ids, response


# Allow POESESSIONID to be passed as an argument
def main():
    # Parse command line arguments, allow to set session id
    parser = argparse.ArgumentParser(description='Fetches active trade offers from Path of Exile\'s public stash API and stores them in a SQLite database.')
    parser.add_argument('-s', '--session', help='POESESSID cookie value to use for fetching trade offers.')
    args = parser.parse_args()

    # Fetch trade offers
    session = None
    trade_ids, response = fetch_trade_offers(session, TRADE_QUERY)
    for trade_id in trade_ids:
        # Fetch the trade offer
        wait_until_can_make_request(response)
        session = get_session_cookie(session, response)
        response = requests.get(TRADE_OFFER_URL.format(trade_id), headers=headers(session), verify=False)
        response.raise_for_status()
        trade_offer = response.json()

        # Print the trade offer
        print(json.dumps(trade_offer, indent=2))
    
if __name__ == '__main__':
    main()
    