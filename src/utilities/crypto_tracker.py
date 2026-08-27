#!/usr/bin/env python3
"""
crypto_tracker.py — Track cryptocurrency prices using CoinGecko API
No API key required, supports multiple coins and currencies
"""

import urllib.request
import json
import argparse
import logging
from typing import Optional, Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

COINGECKO_API = "https://api.coingecko.com/api/v3"

# Common coin IDs
POPULAR_COINS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "bnb": "binancecoin",
    "sol": "solana",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "dot": "polkadot",
    "matic": "matic-network",
    "link": "chainlink"
}


def get_prices(coin_ids: List[str], vs_currencies: List[str] = None) -> Optional[Dict]:
    """Get current prices for coins"""
    if vs_currencies is None:
        vs_currencies = ["usd"]
    
    ids = ",".join(coin_ids)
    vs = ",".join(vs_currencies)
    
    url = f"{COINGECKO_API}/simple/price?ids={ids}&vs_currencies={vs}&include_24hr_change=true&include_market_cap=true"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error(f"Failed to get prices: {e}")
        return None


def get_coin_info(coin_id: str) -> Optional[Dict]:
    """Get detailed coin information"""
    url = f"{COINGECKO_API}/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error(f"Failed to get coin info: {e}")
        return None


def format_price(price: float) -> str:
    """Format price with appropriate precision"""
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.6f}"


def main():
    parser = argparse.ArgumentParser(description="Cryptocurrency Price Tracker")
    parser.add_argument("coins", nargs="*", default=["bitcoin", "ethereum"], help="Coin IDs or symbols (btc, eth, etc.)")
    parser.add_argument("--vs", default="usd", help="vs currencies (comma-separated)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Convert symbols to IDs
    coin_ids = []
    for coin in args.coins:
        coin_lower = coin.lower()
        if coin_lower in POPULAR_COINS:
            coin_ids.append(POPULAR_COINS[coin_lower])
        else:
            coin_ids.append(coin_lower)
    
    vs_currencies = [c.strip() for c in args.vs.split(",")]
    
    prices = get_prices(coin_ids, vs_currencies)
    
    if not prices:
        print("Failed to get prices")
        return
    
    if args.json:
        print(json.dumps(prices, indent=2))
    else:
        print(f"💰 Cryptocurrency Prices")
        print(f"{'='*50}")
        
        for coin_id, data in prices.items():
            print(f"\n{coin_id.upper()}:")
            for currency, price in data.items():
                if currency == "usd_24h_change":
                    change = price
                    emoji = "📈" if change > 0 else "📉"
                    print(f"  24h Change: {emoji} {change:.2f}%")
                elif currency == "usd_market_cap":
                    print(f"  Market Cap: ${price:,.0f}")
                else:
                    print(f"  {currency.upper()}: {format_price(price)}")


if __name__ == "__main__":
    main()