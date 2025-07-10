from binance import Client, ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException
from datetime import datetime
from typing import Dict, List, Optional
from .logger import setup_logger

logger = setup_logger()

class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            self.client.API_URL = 'https://testnet.binancefuture.com'
        self.websocket_manager = None
        self.price_data = {}
        
        try:
            self.client.ping()
            logger.info("Successfully connected to Binance Futures Testnet")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise
    
    def validate_symbol(self, symbol: str) -> bool:
        try:
            info = self.client.get_exchange_info()
            symbols = [s['symbol'] for s in info['symbols'] if s['status'] == 'TRADING']
            return symbol.upper() in symbols
        except Exception as e:
            logger.error(f"Error validating symbol: {e}")
            return False
    
    def get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    def start_price_stream(self, symbols: List[str]):
        def handle_socket_message(msg):
            symbol = msg['s']
            price = float(msg['c'])
            self.price_data[symbol] = {
                'price': price,
                'timestamp': datetime.now()
            }
            logger.debug(f"Price update: {symbol} = {price}")
        
        self.websocket_manager = ThreadedWebsocketManager(
            api_key=self.client.API_KEY,
            api_secret=self.client.API_SECRET,
            testnet=True
        )
        
        self.websocket_manager.start()
        
        for symbol in symbols:
            self.websocket_manager.start_symbol_ticker_socket(
                callback=handle_socket_message,
                symbol=symbol
            )
        
        logger.info(f"Started price stream for {symbols}")
    
    def stop_price_stream(self):
        if self.websocket_manager:
            self.websocket_manager.stop()
            self.websocket_manager = None
            logger.info("Stopped price stream")
    
    def get_account_balance(self) -> Dict:
        try:
            balance = self.client.futures_account_balance()
            return {item['asset']: float(item['balance']) for item in balance}
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        try:
            orders = self.client.futures_get_open_orders(symbol=symbol)
            return orders
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        try:
            order = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            return order
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {}