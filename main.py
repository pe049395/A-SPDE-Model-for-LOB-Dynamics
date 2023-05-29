import json
import websocket

from trader import Trader

class BinanceWebsocketConnector(Trader):
    def __init__(self, symbol):
        super().__init__()

        self.symbol = symbol
        self.ws = websocket.WebSocketApp(
            "wss://stream.binance.com:9443/ws",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        websocket.enableTrace(False)

    def on_open(self, ws):
        print("WebSocket connection opened")
        subscribe_message = {
            "method": "SUBSCRIBE",
            "params":
            [f"{self.symbol.lower()}@depth20@100ms"],
            "id": 1
        }
        self.ws.send(json.dumps(subscribe_message))

    def on_error(self, ws, message):
        print(f"WebSocket error: {message}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def on_message(self, ws, message):
        self.handle_message(message)

def main():
    symbol = "BTCUSDT"
    connector = BinanceWebsocketConnector(symbol)
    connector.ws.run_forever()

if __name__ == "__main__":
    main()
