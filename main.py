# https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3366536

import time
import json
import math
import numpy as np
import os
import certifi
import logging
import websocket

from binance.websocket.spot.websocket_client import SpotWebsocketClient as WebsocketClient
from binance.spot import Spot as Client
from binance.lib.utils import config_logging
from binance.error import ClientError

from binance_client import client, margin_send_market_buy_order, margin_send_market_sell_order

class Trader:
    def __init__(self, window, threshold, dt=0.1, theta=0.01):
        self.window = window
        self.threshold = threshold
        self.dt = dt
        self.theta = theta

        self.ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                    on_message = lambda ws,msg: self.on_message(ws, msg),
                    on_error   = lambda ws,msg: self.on_error(ws, msg),
                    on_close   = lambda ws:     self.on_close(ws),
                    on_open    = lambda ws:     self.on_open(ws))

        self.z0_bid = np.array([])
        self.z0_ask = np.array([])
        self.nu = 1

    def on_open(self, ws):
        print("opened")
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params":
            ["btcusdt@depth20@100ms"],
            "id": 1
            }

        self.ws.send(json.dumps(subscribe_message))

    def on_error(self, ws, message):
        print('error:', message)

    def on_close(self, ws):
        print("closed connection")

    def on_message(self, ws, message, symbol="BTCUSDT"):
        message = json.loads(message)

        # z0값 저장하기
        bids = list(zip(*message['bids']))[1]
        z0_bid_element = sum([int(float(x)*100000000) for x in bids]) # 부동소수점 오류 방지 위해 100000000 곱함
        self.z0_bid = np.append(self.z0_bid, z0_bid_element)

        asks = list(zip(*message['asks']))[1]
        z0_ask_element = sum([int(float(x)*100000000) for x in asks])
        self.z0_ask = np.append(self.z0_ask, z0_ask_element)

        # 파라미터 값 계산하기
        if self.z0_ask.size == self.window+1:
            self.z0_bid, mu_bid, nu_bid = self.estimate_params(self.z0_bid)
            self.z0_ask, mu_ask, nu_ask = self.estimate_params(self.z0_ask)

            if (nu_bid is not None) and (nu_ask is not None):
                expected_midprice_movement = self.theta * (nu_bid * (mu_bid / self.z0_bid[-1] - 1) - nu_ask * (mu_ask / self.z0_ask[-1] - 1)) / 2
                nu = (nu_bid + nu_ask) / 2
                expected_midprice_movement = expected_midprice_movement / nu

            # 거래하는 부분 생략
            now = time.time()
            if expected_midprice_movement >= self.threshold:
                self.last_trade_time = now

            elif expected_midprice_movement <= -self.threshold:
                self.last_trade_time = now

    def estimate_params(self, data):
        est_mu = np.mean(data[1::])
        sum1 = np.sum(np.true_divide(np.square((data[:self.window:] - est_mu)), np.square(data[:self.window:])))
        sum2 = np.sum(np.multiply(np.true_divide((data[:self.window:] - est_mu), np.square(data[:self.window:])),
                              (data[1::] - est_mu)))

        if (sum2 <= 0) or (sum1 <= 0):
            nu = None
        else:
            nu = math.log(sum1 / sum2) / self.dt

        return data[1:], est_mu, nu


if __name__ == "__main__":
    trader = Trader(window=300, threshold=1)
    trader.ws.run_forever()
