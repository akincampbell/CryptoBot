import time
import requests
import hmac
import hashlib
import base64
import json
import os
from dotenv import load_dotenv

# Load API keys from environment variables
load_dotenv()
API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")
ACCOUNT_ID = os.getenv("COINBASE_ACCOUNT_ID")

BASE_URL = "https://api.coinbase.com"

# Trading parameters
BUY_PRICE = 2.20  # Buy when XRP is at or below this price
SELL_PRICE = 2.70  # Sell when XRP is at or above this price
TRADE_AMOUNT_USD = 20  # Amount to buy in USD

# Function to create authentication headers
def get_auth_headers(method, request_path, body=""):
    timestamp = str(int(time.time()))
    message = timestamp + method + request_path + body
    signature = hmac.new(
        API_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    return {
        "CB-ACCESS-KEY": API_KEY,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
    }

# Get the current price of XRP in USD
def get_xrp_price():
    response = requests.get(f"{BASE_URL}/v2/prices/XRP-USD/spot")
    if response.status_code == 200:
        return float(response.json()["data"]["amount"])
    else:
        print("Error fetching XRP price:", response.text)
        return None

# Buy XRP when conditions are met
def buy_xrp():
    order = {
        "type": "market",
        "side": "buy",
        "product_id": "XRP-USD",
        "funds": str(TRADE_AMOUNT_USD),
    }
    response = requests.post(
        f"{BASE_URL}/v2/accounts/{ACCOUNT_ID}/buys",
        headers=get_auth_headers("POST", f"/v2/accounts/{ACCOUNT_ID}/buys", json.dumps(order)),
        json=order,
    )
    return response.json()

# Sell XRP when conditions are met
def sell_xrp():
    xrp_balance = get_xrp_balance()
    if xrp_balance > 0:
        order = {
            "type": "market",
            "side": "sell",
            "product_id": "XRP-USD",
            "size": str(xrp_balance),
        }
        response = requests.post(
            f"{BASE_URL}/v2/accounts/{ACCOUNT_ID}/sells",
            headers=get_auth_headers("POST", f"/v2/accounts/{ACCOUNT_ID}/sells", json.dumps(order)),
            json=order,
        )
        return response.json()
    else:
        print("No XRP to sell.")

# Get XRP balance
def get_xrp_balance():
    response = requests.get(f"{BASE_URL}/v2/accounts", headers=get_auth_headers("GET", "/v2/accounts"))
    if response.status_code == 200:
        accounts = response.json()["data"]
        for acc in accounts:
            if acc["currency"] == "XRP":
                return float(acc["balance"]["amount"])
    return 0

# Main loop to monitor prices and execute trades
def trade_xrp():
    has_xrp = False  # Track whether we currently own XRP

    while True:
        price = get_xrp_price()
        if price:
            print(f"Current XRP Price: ${price:.2f}")

            if not has_xrp and price <= BUY_PRICE:
                print(f"Buying XRP at ${price:.2f}...")
                buy_xrp()
                has_xrp = True  # Mark as holding XRP

            elif has_xrp and price >= SELL_PRICE:
                print(f"Selling XRP at ${price:.2f}...")
                sell_xrp()
                has_xrp = False  # Mark as not holding XRP

        time.sleep(30)  # Wait before checking again

# Run the trading bot
if __name__ == "__main__":
    trade_xrp()
