import os
import logging
from binance.spot import Spot as Client
from binance.error import ClientError

api_key = ""
api_secret = ""

client = Client(api_key, api_secret)

def handle_trade_error(action, error):
    error_text = "Trade error. Action: {}. Status: {}. Error code: {}. Error message: {}".format(
        action, error.status_code, error.error_code, error.error_message
    )
    logging.error(error_text)

def margin_send_market_buy_order(symbol, quantity):
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quantity": quantity,
        "isIsolated": "TRUE",
    }

    try:
        response = client.new_margin_order(**params)
        logging.info(response)
    except ClientError as error:
        handle_trade_error("Market Buy", error)

def margin_send_market_sell_order(symbol, quantity):
    params = {
        "symbol": symbol,
        "side": "SELL",
        "type": "MARKET",
        "quantity": quantity,
        "isIsolated": "TRUE",
    }

    try:
        response = client.new_margin_order(**params)
        logging.info(response)
    except ClientError as error:
        handle_trade_error("Market Sell", error)
