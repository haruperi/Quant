"""Usage example for MT5Client broker client and wrappers."""

import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Add the project root to sys.path to allow direct execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[5])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.brokers.mt5 import (  # noqa: E402
    get_account_info,
    get_history_deal_info,
    get_history_order_info,
    get_mt5_client,
    get_order_info,
    get_position_info,
    get_symbol_info,
    get_terminal_info,
    trade,
)

client = get_mt5_client()

# Shared state across trading examples
trading_symbol = "BTCUSD"
pos_ticket = 0
ord_ticket = 0
buy_price = 0.0
limit_price = 0.0
used_filling_mode = 0


def example_01_connect() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 1. Connecting and Retrieving MT5 Data via Wrappers ---")
    print("=" * 100)

    try:
        client.connect()
    except Exception as e:  # noqa: BLE001
        print(f"Exception during connection: {e}")

    if client.is_connected():
        print("MT5 connection established successfully.")
    else:
        print("Failed to establish MT5 connection.")
    client.shutdown()


def example_02_terminal() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 2. Connecting and Fetching terminal info ---")
    print("=" * 100)

    term_info = get_terminal_info()
    if term_info is not None:
        print(f"Build:              {term_info.build}")
        print(f"Connected:          {'Yes' if term_info.connected else 'No'}")
        print(f"Trade Allowed:      {'Yes' if term_info.trade_allowed else 'No'}")
        print(f"DLLs Allowed:       {'Yes' if term_info.dlls_allowed else 'No'}")
        print(f"Ping Last (us):     {term_info.ping_last}")
        print(f"Language:           {term_info.language}")
        print(f"Company:            {term_info.company}")
        print(f"Name:               {term_info.name}")
        print(f"Path:               {term_info.path}")
        print(f"Data Path:          {term_info.data_path}")
        print(f"Common Data Path:   {term_info.commondata_path}")


def example_03_account() -> None:
    """Demonstrate MT5 Account class."""
    print("\n" + "=" * 100)
    print("--- 3. Connecting and Fetching ACCOUNT INFORMATION  ---")
    print("=" * 100)

    acc_info = get_account_info()
    if acc_info is not None:
        # Display account information
        print(f"Login:          {acc_info.login}")
        print(f"Name:           {acc_info.name}")
        print(f"Server:         {acc_info.server}")
        print(f"Company:        {acc_info.company}")
        print(f"Currency:       {acc_info.currency}")
        print(f"Leverage:       1:{acc_info.leverage}")
        print()

        # Display account mode
        print("ACCOUNT MODE")
        print("-" * 60)
        print(f"Trade Mode:     {acc_info.trade_mode}")
        print(f"Margin Mode:    {acc_info.margin_mode}")
        print()

        # Display account permissions
        print("PERMISSIONS")
        print("-" * 60)
        print(f"Trade Allowed:  {'Yes' if acc_info.trade_allowed else 'No'}")
        print(f"Expert Allowed: {'Yes' if acc_info.trade_expert else 'No'}")
        print(f"Limit Orders:   {acc_info.limit_orders} (0 = unlimited)")
        print()

        # Display account balance and equity
        print("BALANCE & EQUITY")
        print("-" * 60)
        print(f"Balance:        {acc_info.balance:.2f} {acc_info.currency}")
        print(f"Credit:         {acc_info.credit:.2f} {acc_info.currency}")
        print(f"Profit:         {acc_info.profit:.2f} {acc_info.currency}")
        print(f"Equity:         {acc_info.equity:.2f} {acc_info.currency}")
        print()

        # Display margin information
        print("MARGIN INFORMATION")
        print("-" * 60)
        print(f"Margin Used:    {acc_info.margin:.2f} {acc_info.currency}")
        print(f"Free Margin:    {acc_info.margin_free:.2f} {acc_info.currency}")
        if getattr(acc_info, "margin", 0.0) > 0:
            print(f"Margin Level:   {acc_info.margin_level:.2f}%")
        else:
            print("Margin Level:   N/A (no open positions)")
        print(f"Margin Call:    {acc_info.margin_so_call}")
        print(f"Margin Stopout: {acc_info.margin_so_so}")
        print()


def example_04_symbol() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 4. Connecting and Fetching SYMBOL INFORMATION ---")
    print("=" * 100)

    symbol = get_symbol_info("EURUSD")
    if symbol is not None:
        print(f"Symbol:         {symbol.name}")
        print(f"Description:    {symbol.description}")
        print(f"Path:           {symbol.path}")
        print(f"Digits:         {symbol.digits}")
        print(f"Point:          {symbol.point}")
        print(f"Tick Size:      {symbol.trade_tick_size}")

        print("\nCURRENT PRICES")
        print("-" * 60)
        bid = float(symbol.bid or 0.0)
        ask = float(symbol.ask or 0.0)
        last = float(symbol.last or 0.0)
        spread = symbol.spread
        spread_float = symbol.spread_float
        print(f"Bid:            {bid:.{symbol.digits}f}")
        print(f"Ask:            {ask:.{symbol.digits}f}")
        print(f"Last:           {last:.{symbol.digits}f}")
        print(f"Spread:         {spread} points")
        print(f"Spread Float:   {'Yes' if spread_float else 'No'}")

        print("\nTRADING INFORMATION")
        print("-" * 60)
        print(f"Trade Mode:     {symbol.trade_mode}")
        print(f"Execution:      {symbol.trade_exemode}")
        print(f"Calc Mode:      {symbol.trade_calc_mode}")
        print(f"Stops Level:    {symbol.trade_stops_level} points")
        print(f"Freeze Level:   {symbol.trade_freeze_level} points")

        print("\nLOT PARAMETERS")
        print("-" * 60)
        print(f"Contract Size:  {float(symbol.trade_contract_size):.2f}")
        print(f"Min Lot:        {float(symbol.volume_min):.2f}")
        print(f"Max Lot:        {float(symbol.volume_max):.2f}")
        print(f"Lot Step:       {float(symbol.volume_step):.2f}")

        print("\nSWAP INFORMATION")
        print("-" * 60)
        print(f"Swap Mode:      {symbol.swap_mode}")
        print(f"Swap Long:      {float(symbol.swap_long):.2f}")
        print(f"Swap Short:     {float(symbol.swap_short):.2f}")

        print(f"Total symbols: {client.symbols_total()}")


def example_05_position() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 5. Connecting and Fetching position info ---")
    print("=" * 100)

    positions = get_position_info()
    if positions is not None:
        print(f"Active positions count: {len(positions)}")

    for i, position in enumerate(positions):
        print(f"{i + 1}. Ticket {position.ticket}")
        print(f"   Symbol: {position.symbol}")
        print(f"   Type: {position.type}")
        print(f"   Volume: {position.volume}")
        print(f"   Open Price: {position.price_open}")
        print(f"   Current Price: {position.price_current}")
        print(f"   Profit: ${position.profit:.2f}")
        print(f"   Swap: ${position.swap:.2f}")
        print(f"   SL: {position.sl} TP: {position.tp}")
        print(f"   Comment: {position.comment}")
        print("-" * 30)

    print("\n" + "=" * 60)
    print("Selecting by Symbol 'EURUSD'")
    print("=" * 60)
    eur = get_position_info(symbol="EURUSD")
    if eur:
        position = eur[0]
        print("Found EURUSD position:")
        print(f"  Ticket: {position.ticket}")
        print(f"  Profit: {position.profit}")
    else:
        print("No EURUSD position found.")


def example_06_order() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 6. Connecting and Fetching order info ---")
    print("=" * 100)

    orders = get_order_info()
    if orders is not None:
        print(f"Active orders count: {len(orders)}")

    for i, order in enumerate(orders):
        print(f"{i + 1}. Ticket {order.ticket}")
        print(f"   Symbol: {order.symbol}")
        print(f"   Type: {order.type}")
        print(f"   Volume Initial: {order.volume_initial}")
        print(f"   Volume Current: {order.volume_current}")
        print(f"   Open Price: {order.price_open}")
        print(f"   Current Price: {order.price_current}")
        print(f"   SL: {order.sl} TP: {order.tp}")
        print(f"   Comment: {order.comment}")
        print("-" * 30)

    print("\n" + "=" * 60)
    print("Selecting by Symbol 'EURUSD'")
    print("=" * 60)
    eur = get_order_info(symbol="EURUSD")
    if eur:
        order = eur[0]
        print("Found EURUSD order:")
        print(f"  Ticket: {order.ticket}")
        print(f"  State: {order.state}")
    else:
        print("No EURUSD order found.")


def example_07_history_order() -> None:
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 7. Connecting and Fetching history order info ---")
    print("=" * 100)

    start = datetime(1990, 1, 1, tzinfo=UTC)
    end = datetime.now(UTC)
    orders = get_history_order_info(date_from=start, date_to=end)
    if orders is None:
        orders = ()

    total = len(orders)
    print(f"Total orders: {total}\n")

    for i, order in enumerate(orders):
        print(f"{i + 1}. Ticket #{order.ticket} {order.symbol}")
        print(f"   State: {order.state}")
        print(f"   Setup: {order.time_setup}")
        print(f"   Done: {order.time_done}")
        print(f"   Type: {order.type}")
        print(f"   Symbol: {order.symbol}")
        print(f"   Volume: {order.volume_current}/{order.volume_initial}")
        print(f"   Price: {order.price_open}")
        print(f"   SL: {order.sl}, TP: {order.tp}")
        print(f"   Magic: {order.magic}")
        print(f"   Position By ID: {order.position_id}")
        print("-" * 30)

    print("\n" + "=" * 70)
    print("History Order Statistics")
    print("=" * 70)

    filled_count = sum(
        1
        for o in orders
        if int(o.state) == 4  # noqa: PLR2004
    )
    canceled_count = sum(
        1
        for o in orders
        if int(o.state) == 2  # noqa: PLR2004
    )
    total_vol = sum(float(o.volume_initial) for o in orders)
    print(f"Filled: {filled_count}")
    print(f"Canceled: {canceled_count}")
    print(f"Total Volume Ordered: {total_vol:.2f}")

    print("\n" + "=" * 70)
    print("Filter by Group '*USD*'")
    print("=" * 70)
    usd_group = get_history_order_info(date_from=start, date_to=end, group="*USD*")
    usd_group_len = len(usd_group) if usd_group is not None else 0
    print(f"history_orders_get(group='*USD*') -> {usd_group_len} row(s)")

    print("\n" + "=" * 70)
    print("String Representation")
    print("=" * 70)
    if orders:
        print(f"Ticket #{orders[0].ticket} {orders[0].symbol}")


def example_08_history_deal() -> None:  # noqa: PLR0915
    """Demonstrate MT5 Client connection and usage wrapper functions."""
    print("\n" + "=" * 100)
    print("--- 8. Connecting and Fetching history deal info ---")
    print("=" * 100)

    start = datetime(1990, 1, 1, tzinfo=UTC)
    end = datetime.now(UTC)
    deals = get_history_deal_info(date_from=start, date_to=end)
    if deals is None:
        deals = ()

    total_deals = len(deals)
    print(f"Total deals: {total_deals}\n")

    for i, deal in enumerate(deals):
        deal_time = int(deal.time or 0)
        t = datetime.fromtimestamp(deal_time, tz=UTC) if deal_time > 0 else "N/A"
        print(f"{i + 1}. Ticket {deal.ticket}")
        print(f"   Type: {deal.type}")
        print(f"   Entry: {deal.entry}")
        print(f"   Time: {t}")
        print(f"   Price: {deal.price}")
        print(f"   Commission: ${float(deal.commission):.2f}")
        print(f"   Profit: ${float(deal.profit):.2f}")
        print(f"   Magic: {deal.magic}")
        print(f"   Order: {deal.order}")
        print(f"   Position ID: {deal.position_id}")
        print(f"   Time MSC: {deal.time_msc}")
        print(f"   Comment: {deal.comment}")
        print(f"   External ID: {deal.external_id}")
        print("-" * 30)

    print("\n" + "=" * 70)
    print("Trading Statistics")
    print("=" * 70)

    total_profit = sum(float(d.profit) for d in deals)
    total_commission = sum(float(d.commission) for d in deals)
    total_swap = sum(float(d.swap) for d in deals)

    print(f"Total Profit: ${total_profit:.2f}")
    print(f"Total Commission: ${total_commission:.2f}")
    print(f"Total Swap: ${total_swap:.2f}")
    print(f"Net Result: ${total_profit + total_commission + total_swap:.2f}")

    print("\n" + "=" * 70)
    print("Filter by Group '*USD*'")
    print("=" * 70)
    usd_group = get_history_deal_info(date_from=start, date_to=end, group="*USD*")
    usd_group_len = len(usd_group) if usd_group is not None else 0
    print(f"history_deals_get(group='*USD*') -> {usd_group_len} row(s)")

    print("\n" + "=" * 70)
    print("Deals by Symbol (Manual Filter)")
    print("=" * 70)

    target_symbol = "EURUSD"
    print(f"Deals for {target_symbol}:")
    count = 0
    for deal in deals:
        symbol = deal.symbol
        if symbol == target_symbol:
            print(f"  #{deal.ticket} {deal.type} {deal.volume} lots P/L: {deal.profit}")
            count += 1
    if count == 0:
        print("  No deals found.")


def example_09_open_position() -> None:
    """Demonstrate opening a position (Buy 0.02 EURUSD)."""
    global pos_ticket, buy_price, used_filling_mode  # noqa: PLW0603
    print("\n" + "=" * 100)
    print("--- 9. Opening a Position (Buy 0.02 EURUSD) ---")
    print("=" * 100)

    sym_info = get_symbol_info(trading_symbol)
    if sym_info is None:
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    # Dynamically select filling mode based on symbol properties via client delegation
    # (using integer flags for SYMBOL_FILLING_FOK=1, SYMBOL_FILLING_IOC=2)
    used_filling_mode = client.ORDER_FILLING_FOK
    if sym_info.filling_mode & 2:  # SYMBOL_FILLING_IOC
        used_filling_mode = client.ORDER_FILLING_IOC
    elif sym_info.filling_mode & 1:  # SYMBOL_FILLING_FOK
        used_filling_mode = client.ORDER_FILLING_FOK

    tick = client.symbol_info_tick(trading_symbol)
    if tick is None:
        print(f"Failed to fetch current tick for {trading_symbol}")
        return
    buy_price = tick.ask

    request = {
        "action": client.TRADE_ACTION_DEAL,
        "symbol": trading_symbol,
        "volume": 0.02,
        "type": client.ORDER_TYPE_BUY,
        "price": buy_price,
        "deviation": 20,
        "magic": 99999,
        "comment": "Open Position Demo",
        "type_time": client.ORDER_TIME_GTC,
        "type_filling": used_filling_mode,
    }

    try:
        result = trade(request)
        pos_ticket = result.order
        print(f"Position successfully opened! Ticket: {pos_ticket}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to open position: {e}")


def example_10_calc_profit_margin() -> None:
    """Demonstrate profit and margin calculations via client delegation."""
    print("\n" + "=" * 100)
    print("--- 10. Calculating Profit and Margin ---")
    print("=" * 100)

    if not client.is_connected():
        print("Client not connected.")
        return

    sym_info = get_symbol_info(trading_symbol)
    if sym_info is None:
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    tick = client.symbol_info_tick(trading_symbol)
    if tick is None:
        print("Failed to fetch current tick.")
        return

    # Calculate margin required for BUY 0.02 EURUSD using client delegation
    margin = client.order_calc_margin(
        client.ORDER_TYPE_BUY, trading_symbol, 0.02, tick.ask
    )
    if margin is not None:
        print(f"Margin required for 0.02 {trading_symbol} Buy: ${margin:.2f}")
    else:
        err = client.last_error()
        print(f"Failed to calculate margin. Error: {err}")

    # Calculate expected profit if price moves up by 100 pips
    # using client delegation
    pip_value = sym_info.point * 10
    target_price = round(tick.ask + (100 * pip_value), sym_info.digits)
    profit = client.order_calc_profit(
        client.ORDER_TYPE_BUY, trading_symbol, 0.02, tick.ask, target_price
    )
    if profit is not None:
        print(f"Expected profit if price moves up by 100 pips: ${profit:.2f}")
    else:
        err = client.last_error()
        print(f"Failed to calculate profit. Error: {err}")


def example_11_modify_position() -> None:
    """Demonstrate modifying SL/TP of a position."""
    print("\n" + "=" * 100)
    print("--- 11. Modifying Position (Set SL/TP) ---")
    print("=" * 100)

    time.sleep(5)

    if pos_ticket == 0:
        print("No active position ticket from Example 9. Skipping modification.")
        return

    sym_info = get_symbol_info(trading_symbol)
    if sym_info is None:
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    pip_value = sym_info.point * 10

    # Set Stop Loss 100 pips below buy price, and Take Profit 100 pips above
    sl_price = buy_price - (1000 * pip_value)
    tp_price = buy_price + (1000 * pip_value)

    request = {
        "action": client.TRADE_ACTION_SLTP,
        "symbol": trading_symbol,
        "position": pos_ticket,
        "sl": round(sl_price, sym_info.digits),
        "tp": round(tp_price, sym_info.digits),
    }

    try:
        result = trade(request)
        print(f"Position modified successfully! Ticket: {result.order}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to modify position: {e}")


def example_12_close_partial_position() -> None:
    """Demonstrate closing a partial position."""
    print("\n" + "=" * 100)
    print("--- 12. Closing Partial Position (Close 0.01) ---")
    print("=" * 100)

    time.sleep(5)

    if pos_ticket == 0:
        print("No active position ticket from Example 9. Skipping partial close.")
        return

    tick = client.symbol_info_tick(trading_symbol)
    if tick is None:
        print("Failed to fetch tick.")
        return

    request = {
        "action": client.TRADE_ACTION_DEAL,
        "symbol": trading_symbol,
        "volume": 0.01,
        "type": client.ORDER_TYPE_SELL,  # Close buy with sell
        "position": pos_ticket,
        "price": tick.bid,
        "deviation": 20,
        "magic": 99999,
        "comment": "Partial Close Demo",
        "type_time": client.ORDER_TIME_GTC,
        "type_filling": used_filling_mode,
    }

    try:
        result = trade(request)
        print(f"Partial position closed successfully! Deal Ticket: {result.deal}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to partially close position: {e}")


def example_13_close_position() -> None:
    """Demonstrate closing the remaining position."""
    print("\n" + "=" * 100)
    print("--- 13. Closing Remaining Position (Close 0.01) ---")
    print("=" * 100)

    time.sleep(5)

    if pos_ticket == 0:
        print("No active position ticket from Example 9. Skipping close.")
        return

    tick = client.symbol_info_tick(trading_symbol)
    if tick is None:
        print("Failed to fetch tick.")
        return

    request = {
        "action": client.TRADE_ACTION_DEAL,
        "symbol": trading_symbol,
        "volume": 0.01,  # remaining 0.01
        "type": client.ORDER_TYPE_SELL,
        "position": pos_ticket,
        "price": tick.bid,
        "deviation": 20,
        "magic": 99999,
        "comment": "Full Close Demo",
        "type_time": client.ORDER_TIME_GTC,
        "type_filling": used_filling_mode,
    }

    try:
        result = trade(request)
        print(f"Position closed fully! Deal Ticket: {result.deal}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to close remaining position: {e}")


def example_14_pending_orders() -> None:
    """Demonstrate placing a pending order (Buy Limit)."""
    global ord_ticket, limit_price  # noqa: PLW0603
    print("\n" + "=" * 100)
    print("--- 14. Placing Pending Order (Buy Limit) ---")
    print("=" * 100)

    time.sleep(5)

    sym_info = get_symbol_info(trading_symbol)
    if sym_info is None:
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    tick = client.symbol_info_tick(trading_symbol)
    if tick is None:
        print("Failed to fetch tick.")
        return

    pip_value = sym_info.point * 10

    # Place Buy Limit 200 pips below current bid to avoid instant execution
    limit_price = tick.bid - (200 * pip_value)

    request = {
        "action": client.TRADE_ACTION_PENDING,
        "symbol": trading_symbol,
        "volume": 0.01,
        "type": client.ORDER_TYPE_BUY_LIMIT,
        "price": round(limit_price, sym_info.digits),
        "deviation": 20,
        "magic": 99999,
        "comment": "Buy Limit Demo",
        "type_time": client.ORDER_TIME_GTC,
        "type_filling": used_filling_mode,
    }

    try:
        result = trade(request)
        ord_ticket = result.order
        print(f"Pending order placed! Ticket: {ord_ticket}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to place pending order: {e}")


def example_15_modify_pending_orders() -> None:
    """Demonstrate modifying a pending order."""
    print("\n" + "=" * 100)
    print("--- 15. Modifying Pending Order ---")
    print("=" * 100)

    time.sleep(5)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping modification.")
        return

    sym_info = get_symbol_info(trading_symbol)
    if sym_info is None:
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    pip_value = sym_info.point * 10

    # Move the limit price 50 pips lower
    new_limit_price = limit_price - (50 * pip_value)

    request = {
        "action": client.TRADE_ACTION_MODIFY,
        "order": ord_ticket,
        "price": round(new_limit_price, sym_info.digits),
        "sl": 0.0,
        "tp": 0.0,
    }

    try:
        result = trade(request)
        print(f"Pending order modified successfully! Ticket: {result.order}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to modify pending order: {e}")


def example_16_delete_pending_orders() -> None:
    """Demonstrate deleting a pending order."""
    print("\n" + "=" * 100)
    print("--- 16. Deleting Pending Order ---")
    print("=" * 100)

    time.sleep(5)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping deletion.")
        return

    request = {
        "action": client.TRADE_ACTION_REMOVE,
        "order": ord_ticket,
    }

    try:
        result = trade(request)
        print(f"Pending order deleted successfully! Ticket: {result.order}")
    except Exception as e:  # noqa: BLE001
        print(f"Failed to delete pending order: {e}")


def example_17_shutdown() -> None:
    """Demonstrate shutting down the MT5 terminal connection."""
    print("\n" + "=" * 100)
    print("--- 17. Shutting down MT5 Connection ---")
    print("=" * 100)

    get_mt5_client().shutdown()
    print("MT5 connection shut down.")


if __name__ == "__main__":
    example_01_connect()
    example_02_terminal()
    example_03_account()
    example_04_symbol()
    example_05_position()
    example_06_order()
    example_07_history_order()
    example_08_history_deal()
    example_09_open_position()
    example_10_calc_profit_margin()
    example_11_modify_position()
    example_12_close_partial_position()
    example_13_close_position()
    example_14_pending_orders()
    example_15_modify_pending_orders()
    example_16_delete_pending_orders()
    example_17_shutdown()
