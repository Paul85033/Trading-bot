import streamlit as st
from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.logger import setup_logger
from dotenv import load_dotenv
import os

logger = setup_logger()

load_dotenv()

def main():
    st.set_page_config(page_title="Trading Bot", layout="wide")
    
    st.title("Binance Trading Bot")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    if not api_key or not api_secret:
        st.error("Error fetching API credentials")
        return
    
    try:
        if 'bot' not in st.session_state:
            client = BinanceClient(api_key, api_secret, testnet=True)
            st.session_state.bot = OrderManager(client)
        bot = st.session_state.bot
    except Exception as e:
        st.error(f"Failed to initialize bot: {e}")
        return
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Basic Orders", "Advanced Orders", "TWAP", "Grid", "Account Information"])
    
    with tab1:
        st.header("Basic Orders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Market Order")
            symbol = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="market_symbol")
            side = st.selectbox("Side", ["BUY", "SELL"], key="market_side")
            quantity = st.number_input("Quantity", min_value=0.001, key="market_quantity")
            
            if st.button("Place Order", key="place_order_1"):
                result = bot.place_market_order(symbol, side, quantity)
                if result.error_message:
                    st.error(f"Error: {result.error_message}")
                else:
                    st.success(f"Order placed successfully! Order ID: {result.order_id}")
        
        with col2:
            st.subheader("Limit Order")
            symbol_limit = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="limit_symbol")
            side_limit = st.selectbox("Side", ["BUY", "SELL"], key="limit_side")
            quantity_limit = st.number_input("Quantity", min_value=0.001, key="limit_quantity")
            price_limit = st.number_input("Price", min_value=0.01, key="limit_price")
            
            if st.button("Place Order", key="place_order_2"):
                result = bot.place_limit_order(symbol_limit, side_limit, quantity_limit, price_limit)
                if result.error_message:
                    st.error(f"Error: {result.error_message}")
                else:
                    st.success(f"Order placed successfully! Order ID: {result.order_id}")
    
    with tab2:
        st.header("Advanced Orders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stop-Limit ")
            symbol_stop = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="stop_symbol")
            side_stop = st.selectbox("Side", ["BUY", "SELL"], key="stop_side")
            quantity_stop = st.number_input("Quantity", min_value=0.001, key="stop_quantity")
            stop_price = st.number_input("Stop Price", min_value=0.01, key="stop_price")
            limit_price_stop = st.number_input("Limit Price", min_value=0.01, key="stop_limit_price")
            
            if st.button("Place Order", key="place_order_3"):
                result = bot.place_stop_limit_order(symbol_stop, side_stop, quantity_stop, stop_price, limit_price_stop)
                if result.error_message:
                    st.error(f"Error: {result.error_message}")
                else:
                    st.success(f"Order placed successfully! Order ID: {result.order_id}")
        
        with col2:
            st.subheader("OCO")
            symbol_oco = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="oco_symbol")
            side_oco = st.selectbox("Side", ["BUY", "SELL"], key="oco_side")
            quantity_oco = st.number_input("Quantity", min_value=0.001, key="oco_quantity")
            price_oco = st.number_input("Limit Price", min_value=0.01, key="oco_price")
            stop_price_oco = st.number_input("Stop Price", min_value=0.01, key="oco_stop_price")
            stop_limit_price_oco = st.number_input("Stop Limit Price", min_value=0.01, key="oco_stop_limit_price")
            
            if st.button("Place Order", key="place_order_4"):
                result = bot.place_oco_order(symbol_oco, side_oco, quantity_oco, price_oco, stop_price_oco, stop_limit_price_oco)
                if result.error_message:
                    st.error(f"Error: {result.error_message}")
                else:
                    st.success(f"Order placed successfully! Order ID: {result.order_id}")
    
    with tab3:
        st.header("TWAP")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_twap = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="twap_symbol")
            side_twap = st.selectbox("Side", ["BUY", "SELL"], key="twap_side")
            total_quantity = st.number_input("Total Quantity", min_value=0.001, key="twap_total_quantity")
            duration_minutes = st.number_input("Duration (minutes)", min_value=1, value=10, key="twap_duration")
            interval_seconds = st.number_input("Interval (seconds)", min_value=10, value=60, key="twap_interval")
            
            if st.button("Start", key="start_1"):
                twap_id = bot.start_twap_order(symbol_twap, side_twap, total_quantity, duration_minutes, interval_seconds)
                st.success(f"Order started! ID: {twap_id}")
        
        with col2:
            st.subheader("Active Orders")
            if hasattr(bot, 'twap_orders'):
                for twap_id, order in bot.twap_orders.items():
                    if order['active']:
                        st.write(f"**{twap_id}**")
                        st.write(f"Symbol: {order['symbol']}")
                        st.write(f"Side: {order['side']}")
                        st.write(f"Remaining: {order['remaining_quantity']:.4f}")
                        st.write(f"Orders executed: {len(order['orders'])}")
                        st.write("---")
    
    with tab4:
        st.header("Grid")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_grid = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="grid_symbol")
            lower_price = st.number_input("Lower Price", min_value=0.01, key="grid_lower")
            upper_price = st.number_input("Upper Price", min_value=0.01, key="grid_upper")
            grid_levels = st.number_input("Grid Levels", min_value=3, value=10, key="grid_levels")
            quantity_per_level = st.number_input("Quantity per Level", min_value=0.001, key="grid_quantity")
            
            if st.button("Start", key="start_2"):
                grid_id = bot.start_grid_strategy(symbol_grid, lower_price, upper_price, grid_levels, quantity_per_level)
                st.success(f"Grid started! ID: {grid_id}")
        
        with col2:
            st.subheader("Active Grid ")
            if hasattr(bot, 'grid_orders'):
                for grid_id, order in bot.grid_orders.items():
                    if order['active']:
                        st.write(f"**{grid_id}**")
                        st.write(f"Symbol: {order['symbol']}")
                        st.write(f"Price range: {order['lower_price']:.2f} - {order['upper_price']:.2f}")
                        st.write(f"Active orders: {len(order['active_orders'])}")
                        st.write("---")
    
    with tab5:
        st.header("Account Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Account Balance")
            if st.button("Refresh Balance"):
                balance = bot.client.get_account_balance()
                st.session_state.balance = balance
            
            if 'balance' in st.session_state:
                for asset, amount in st.session_state.balance.items():
                    if amount > 0:
                        st.write(f"{asset}: {amount:.4f}")
        
        with col2:
            st.subheader("Open Orders")
            symbol_orders = st.selectbox("Symbol", ["BTCUSDT", "ETHUSDT"], key="orders_symbol")
            
            if st.button("Get Open Orders"):
                orders = bot.client.get_open_orders(symbol_orders if symbol_orders else None)
                st.session_state.open_orders = orders
            
            if 'open_orders' in st.session_state:
                for order in st.session_state.open_orders:
                    st.write(f"**Order ID:** {order['orderId']}")
                    st.write(f"Symbol: {order['symbol']}")
                    st.write(f"Side: {order['side']}")
                    st.write(f"Type: {order['type']}")
                    st.write(f"Quantity: {order['origQty']}")
                    st.write(f"Price: {order['price']}")
                    st.write(f"Status: {order['status']}")
                    st.write("---")
    
    st.sidebar.header("Live Prices")
    symbols_to_watch = st.sidebar.multiselect("Sream Live Prices", ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOGEUSDT"])
    
    if symbols_to_watch:
        if st.sidebar.button("Start Stream"):
            bot.client.start_price_stream(symbols_to_watch)
            st.sidebar.success("Price stream started!")
        
        if st.sidebar.button("Stop Stream"):
            bot.client.stop_price_stream()
            st.sidebar.success("Price stream stopped!")
        
        if hasattr(bot.client, 'price_data') and bot.client.price_data:
            for symbol, data in bot.client.price_data.items():
                st.sidebar.write(f"{symbol}: ${data['price']:.2f}")

if __name__ == "__main__":
    main()