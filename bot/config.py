from enum import Enum

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_MARKET"
    OCO = "OCO"
    TWAP = "TWAP"
    GRID = "GRID"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"
