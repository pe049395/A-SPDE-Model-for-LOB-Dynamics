import json
import websocket
import math
import numpy as np

from binance_client import client, margin_send_market_buy_order, margin_send_market_sell_order

class Trader:
    def __init__(self, window=300, threshold=0.5, dt=0.1, theta=0.01):
        self.qty = 0.001

        self.window = window
        self.threshold = threshold
        self.dt = dt
        self.theta = theta

        self.z0_bid = np.array([])
        self.z0_ask = np.array([])
        self.nu = 1
        self.expected_midprice_movement = 0
        self.prev_expected_midprice_movement = 0

        self.in_long_position = False
        self.in_short_position = False

    def message_handler(self, message):
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
                self.prev_expected_midprice_movement = self.expected_midprice_movement
                self.expected_midprice_movement = self.theta * (nu_bid * (mu_bid / self.z0_bid[-1] - 1) - nu_ask * (mu_ask / self.z0_ask[-1] - 1)) / 2

            self.execute_trades()

    def execute_trades(self):
        in_position = self.in_long_position or self.in_short_position

        if self.expected_midprice_movement > self.threshold and not in_position:
            margin_send_market_buy_order(self.symbol, self.qty)
            self.in_long_position = True

        elif self.expected_midprice_movement < -self.threshold and not in_position:
            margin_send_market_sell_order(self.symbol, self.qty)
            self.in_short_position = True

        elif self.expected_midprice_movement * self.prev_expected_midprice_movement < 0:
            if self.expected_midprice_movement > 0 and self.in_short_position:
                margin_send_market_buy_order(self.symbol, self.qty)
                self.in_short_position = False

            if self.expected_midprice_movement < 0 and self.in_long_position:
                margin_send_market_sell_order(self.symbol, self.qty)
                self.in_long_position = False
            
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
