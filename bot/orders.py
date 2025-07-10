from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from binance.exceptions import BinanceOrderException
import time
import threading
from .config import OrderType, OrderSide
from .client import BinanceClient
from .logger import setup_logger

logger = setup_logger()

@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    timestamp: datetime
    error_message: Optional[str] = None

class OrderManager:
    def __init__(self, client: BinanceClient):
        self.client = client
        self.active_orders = {}
        self.twap_orders = {}
        self.grid_orders = {}
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        try:
            logger.info(f"Placing {side} market order: {quantity} {symbol}")
            
            order = self.client.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=OrderType.MARKET.value,
                quantity=quantity
            )
            
            logger.info(f"Market order placed successfully: {order}")
            
            return OrderResult(
                order_id=str(order['orderId']),
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET.value,
                quantity=quantity,
                price=None,
                status=order['status'],
                timestamp=datetime.now()
            )
            
        except BinanceOrderException as e:
            logger.error(f"Order error: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET.value,
                quantity=quantity,
                price=None,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error placing market order: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET.value,
                quantity=quantity,
                price=None,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> OrderResult:
        try:
            logger.info(f"Placing {side} limit order: {quantity} {symbol} at {price}")
            
            order = self.client.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=OrderType.LIMIT.value,
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            
            logger.info(f"Limit order placed successfully: {order}")
            
            return OrderResult(
                order_id=str(order['orderId']),
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT.value,
                quantity=quantity,
                price=price,
                status=order['status'],
                timestamp=datetime.now()
            )
            
        except BinanceOrderException as e:
            logger.error(f"Order error: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT.value,
                quantity=quantity,
                price=price,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error placing limit order: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT.value,
                quantity=quantity,
                price=price,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                             stop_price: float, limit_price: float) -> OrderResult:
        try:
            logger.info(f"Placing {side} stop-limit order: {quantity} {symbol} stop: {stop_price} limit: {limit_price}")
            
            order = self.client.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                quantity=quantity,
                stopPrice=stop_price,
                timeInForce='GTC'
            )
            
            logger.info(f"Stop-limit order placed successfully: {order}")
            
            return OrderResult(
                order_id=str(order['orderId']),
                symbol=symbol,
                side=side,
                order_type='STOP_MARKET',
                quantity=quantity,
                price=stop_price,
                status=order['status'],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error placing stop-limit order: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type='STOP_MARKET',
                quantity=quantity,
                price=stop_price,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def place_oco_order(self, symbol: str, side: str, quantity: float, 
                       price: float, stop_price: float, stop_limit_price: float) -> OrderResult:
        try:
            logger.info(f"Placing {side} OCO order: {quantity} {symbol}")
            
            limit_order = self.place_limit_order(symbol, side, quantity, price)
            
            if limit_order.status != "FAILED":
                self.active_orders[limit_order.order_id] = {
                    'type': 'OCO',
                    'stop_price': stop_price,
                    'stop_limit_price': stop_limit_price,
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity
                }
            
            return limit_order
            
        except Exception as e:
            logger.error(f"Error placing OCO order: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type='OCO',
                quantity=quantity,
                price=price,
                status="FAILED",
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def start_twap_order(self, symbol: str, side: str, total_quantity: float, 
                        duration_minutes: int, interval_seconds: int = 60) -> str:
        twap_id = f"twap_{symbol}_{int(time.time())}"
        
        self.twap_orders[twap_id] = {
            'symbol': symbol,
            'side': side,
            'total_quantity': total_quantity,
            'remaining_quantity': total_quantity,
            'duration_minutes': duration_minutes,
            'interval_seconds': interval_seconds,
            'start_time': datetime.now(),
            'orders': [],
            'active': True
        }
        
        threading.Thread(target=self._execute_twap, args=(twap_id,), daemon=True).start()
        
        logger.info(f"Started TWAP order {twap_id}")
        return twap_id
    
    def _execute_twap(self, twap_id: str):
        twap_order = self.twap_orders[twap_id]
        
        total_intervals = (twap_order['duration_minutes'] * 60) // twap_order['interval_seconds']
        quantity_per_interval = twap_order['total_quantity'] / total_intervals
        
        for i in range(total_intervals):
            if not twap_order['active']:
                break
                
            if twap_order['remaining_quantity'] <= 0:
                break
            
            order_quantity = min(quantity_per_interval, twap_order['remaining_quantity'])
            
            result = self.place_market_order(
                twap_order['symbol'],
                twap_order['side'],
                order_quantity
            )
            
            twap_order['orders'].append(result)
            twap_order['remaining_quantity'] -= order_quantity
            
            logger.info(f"TWAP {twap_id}: Executed {order_quantity}, remaining: {twap_order['remaining_quantity']}")
            
            time.sleep(twap_order['interval_seconds'])
        
        twap_order['active'] = False
        logger.info(f"TWAP order {twap_id} completed")
    
    def start_grid_strategy(self, symbol: str, lower_price: float, upper_price: float, 
                          grid_levels: int, quantity_per_level: float) -> str:
        grid_id = f"grid_{symbol}_{int(time.time())}"
        
        price_step = (upper_price - lower_price) / (grid_levels - 1)
        buy_levels = []
        sell_levels = []
        
        current_price = self.client.get_current_price(symbol)
        
        for i in range(grid_levels):
            level_price = lower_price + (i * price_step)
            
            if level_price < current_price:
                buy_levels.append(level_price)
            else:
                sell_levels.append(level_price)
        
        self.grid_orders[grid_id] = {
            'symbol': symbol,
            'lower_price': lower_price,
            'upper_price': upper_price,
            'grid_levels': grid_levels,
            'quantity_per_level': quantity_per_level,
            'buy_levels': buy_levels,
            'sell_levels': sell_levels,
            'active_orders': [],
            'active': True
        }
        
        self._place_grid_orders(grid_id)
        
        logger.info(f"Started grid strategy {grid_id}")
        return grid_id
    
    def _place_grid_orders(self, grid_id: str):
        grid_order = self.grid_orders[grid_id]
        
        for price in grid_order['buy_levels']:
            result = self.place_limit_order(
                grid_order['symbol'],
                OrderSide.BUY.value,
                grid_order['quantity_per_level'],
                price
            )
            if result.status != "FAILED":
                grid_order['active_orders'].append(result)
        
        for price in grid_order['sell_levels']:
            result = self.place_limit_order(
                grid_order['symbol'],
                OrderSide.SELL.value,
                grid_order['quantity_per_level'],
                price
            )
            if result.status != "FAILED":
                grid_order['active_orders'].append(result)