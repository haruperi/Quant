# ruff: noqa: E501, BLE001, E402, PLW0603, SLF001, ANN401
"""Unified usage example for generic Trade classes working with MT5 and cTrader."""

import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import settings
from app.services.trader import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    Trade,
)
from app.services.trader.resolver import get_broker_module

# Shared state across trading examples
trading_symbol = "EURUSD"
pos_ticket = 0
ord_ticket = 0
buy_price = 0.0
limit_price = 0.0
used_filling_mode = 0


def get_client() -> Any:
    """Helper to fetch the underlying broker client."""
    broker = get_broker_module()
    return (
        broker.get_ctrader_client()
        if hasattr(broker, "get_ctrader_client")
        else broker.get_mt5_client()
    )


def example_01_connect() -> None:
    """Demonstrate connection to the active broker."""
    print("\n" + "=" * 100)
    print(f"--- 1. Connecting to Active Broker: {settings.active_broker.upper()} ---")
    print("=" * 100)

    client = get_client()
    try:
        client.connect()
    except Exception as e:
        print(f"Exception during connection: {e}")

    if client.is_connected():
        print(f"Successfully connected to {settings.active_broker.upper()}.")
    else:
        print(f"Failed to connect to {settings.active_broker.upper()}.")


def example_02_terminal() -> None:
    """Demonstrate printing terminal information using TerminalInfo."""
    print("\n" + "=" * 100)
    print("--- 2. Fetching Terminal Info ---")
    print("=" * 100)

    term = TerminalInfo()
    try:
        print(f"Name:             {term.name()}")
        print(f"Company:          {term.company()}")
        print(f"Build:            {term.build()}")
        print(f"Language:         {term.language()}")
        print(f"Connected:        {'Yes' if term.connected() else 'No'}")
        print(f"Trade Allowed:    {'Yes' if term.trade_allowed() else 'No'}")
        print(f"DLLs Allowed:     {'Yes' if term.dlls_allowed() else 'No'}")
        print(f"Ping Last (us):   {term.ping_last()}")
        print(f"Path:             {term.path()}")
        print(f"Data Path:        {term.data_path()}")
        print(f"Common Data Path: {term.common_data_path()}")
    except Exception as e:
        print(f"Failed to fetch terminal info: {e}")


def example_03_account() -> None:
    """Demonstrate printing account information using AccountInfo."""
    print("\n" + "=" * 100)
    print("--- 3. Fetching Account Information ---")
    print("=" * 100)

    acc = AccountInfo()
    try:
        print(f"Login:            {acc.login()}")
        print(f"Name:             {acc.name()}")
        print(f"Server:           {acc.server()}")
        print(f"Company:          {acc.company()}")
        print(f"Currency:         {acc.currency()}")
        print(f"Leverage:         1:{acc.leverage()}")
        print()
        print("ACCOUNT MODE")
        print("-" * 60)
        print(f"Trade Mode:       {acc.trade_mode()} ({acc.trade_mode_description()})")
        print(
            f"Margin Mode:      {acc.margin_mode()} ({acc.margin_mode_description()})"
        )
        print()
        print("PERMISSIONS")
        print("-" * 60)
        print(f"Trade Allowed:    {'Yes' if acc.trade_allowed() else 'No'}")
        print(f"Expert Allowed:   {'Yes' if acc.trade_expert() else 'No'}")
        print(f"Limit Orders:     {acc.limit_orders()} (0 = unlimited)")
        print()
        print("BALANCE & EQUITY")
        print("-" * 60)
        print(f"Balance:          {acc.balance():.2f} {acc.currency()}")
        print(f"Credit:           {acc.credit():.2f} {acc.currency()}")
        print(f"Profit:           {acc.profit():.2f} {acc.currency()}")
        print(f"Equity:           {acc.equity():.2f} {acc.currency()}")
        print()
        print("MARGIN INFORMATION")
        print("-" * 60)
        print(f"Margin Used:      {acc.margin():.2f} {acc.currency()}")
        print(f"Free Margin:      {acc.free_margin():.2f} {acc.currency()}")
        if acc.margin() > 0:
            print(f"Margin Level:     {acc.margin_level():.2f}%")
        else:
            print("Margin Level:     N/A (no open positions)")
        print(f"Margin Stopout:   {acc.margin_so_level()}")
    except Exception as e:
        print(f"Failed to fetch account info: {e}")


def example_04_symbol() -> None:
    """Demonstrate printing symbol specification info using SymbolInfo."""
    print("\n" + "=" * 100)
    print(f"--- 4. Fetching Symbol Information for {trading_symbol} ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    try:
        if sym.refresh():
            print(f"Symbol:           {sym.name()}")
            print(f"Digits:           {sym.digits()}")
            print(f"Point:            {sym.point()}")
            print(f"Tick Size:        {sym.tick_size()}")
            print("\nCURRENT PRICES")
            print("-" * 60)
            print(f"Bid:              {sym.bid():.{sym.digits()}f}")
            print(f"Ask:              {sym.ask():.{sym.digits()}f}")
            print(f"Last:             {sym.last():.{sym.digits()}f}")
            print(f"Spread:           {sym.spread()} points")
            print("\nTRADING INFORMATION")
            print("-" * 60)
            print(
                f"Trade Mode:       {sym.trade_mode()} ({sym.trade_mode_description()})"
            )
            print("\nLOT PARAMETERS")
            print("-" * 60)
            print(f"Contract Size:    {sym.contract_size():.2f}")
            print(f"Min Lot:          {sym.volume_min():.2f}")
            print(f"Max Lot:          {sym.volume_max():.2f}")
            print(f"Lot Step:         {sym.volume_step():.2f}")
            print("\nSWAP INFORMATION")
            print("-" * 60)
            print(f"Swap Mode:        {sym.swap_mode()}")
            print(f"Swap Long:        {sym.swap_long():.2f}")
            print(f"Swap Short:       {sym.swap_short():.2f}")
        else:
            print(f"Failed to refresh symbol specifications for {trading_symbol}")
    except Exception as e:
        print(f"Failed to fetch symbol info: {e}")


def example_05_position() -> None:
    """Demonstrate printing open position list using PositionInfo."""
    print("\n" + "=" * 100)
    print("--- 5. Fetching Active Positions ---")
    print("=" * 100)

    try:
        broker = get_broker_module()
        positions = broker.get_position_info() or ()
        print(f"Active positions count: {len(positions)}")

        pos = PositionInfo()
        for i, raw_pos in enumerate(positions):
            if pos.select_by_ticket(raw_pos.ticket):
                print(f"{i + 1}. Ticket {pos.ticket()}")
                print(f"   Symbol:        {pos.symbol()}")
                print(f"   Type:          {pos.type()} ({pos.type_description()})")
                print(f"   Volume:        {pos.volume()}")
                print(f"   Open Price:    {pos.price_open()}")
                print(f"   Current Price: {pos.price_current()}")
                print(f"   Profit:        ${pos.profit():.2f}")
                print(f"   Swap:          ${pos.swap():.2f}")
                print(f"   SL / TP:       {pos.stop_loss()} / {pos.take_profit()}")
                print(f"   Comment:       {pos.comment()}")
                print("-" * 30)

        print("\nSelecting position by symbol 'EURUSD'...")
        eur_pos = PositionInfo()
        if eur_pos.select("EURUSD"):
            print("Successfully selected EURUSD position:")
            print(f"  Ticket:         {eur_pos.ticket()}")
            print(f"  Profit:         ${eur_pos.profit():.2f}")
        else:
            print("No active EURUSD position found.")
    except Exception as e:
        print(f"Failed to select positions: {e}")


def example_06_order() -> None:
    """Demonstrate printing pending orders list using OrderInfo."""
    print("\n" + "=" * 100)
    print("--- 6. Fetching Active Pending Orders ---")
    print("=" * 100)

    try:
        broker = get_broker_module()
        orders = broker.get_order_info() or ()
        print(f"Active pending orders count: {len(orders)}")

        ord_info = OrderInfo()
        for i, raw_ord in enumerate(orders):
            if ord_info.select(raw_ord.ticket):
                print(f"{i + 1}. Ticket {ord_info.ticket()}")
                print(f"   Symbol:        {ord_info.symbol()}")
                print(
                    f"   Type:          {ord_info.type()} ({ord_info.type_description()})"
                )
                print(f"   Volume Init:   {ord_info.volume_initial()}")
                print(f"   Volume Curr:   {ord_info.volume_current()}")
                print(f"   Open Price:    {ord_info.price_open()}")
                print(f"   Current Price: {ord_info.price_current()}")
                print(
                    f"   SL / TP:       {ord_info.stop_loss()} / {ord_info.take_profit()}"
                )
                print(f"   Comment:       {ord_info.comment()}")
                print("-" * 30)
    except Exception as e:
        print(f"Failed to select pending orders: {e}")


def example_07_history_order() -> None:
    """Demonstrate listing historical orders using HistoryOrderInfo."""
    print("\n" + "=" * 100)
    print("--- 7. Fetching History Orders ---")
    print("=" * 100)

    try:
        start = datetime(1990, 1, 1, tzinfo=UTC)
        end = datetime.now(UTC)
        broker = get_broker_module()
        orders = broker.get_history_order_info(date_from=start, date_to=end) or ()
        print(f"Total historical orders found: {len(orders)}")

        hist = HistoryOrderInfo()
        for i, raw_ord in enumerate(orders[:5]):  # Print up to 5 orders
            if hist.select(raw_ord.ticket):
                print(f"{i + 1}. Ticket #{hist.ticket()} {hist.symbol()}")
                print(f"   Type:          {hist.type()} ({hist.type_description()})")
                print(f"   State:         {hist.state()} ({hist.state_description()})")
                print(
                    f"   Volume:        {hist.volume_current()}/{hist.volume_initial()}"
                )
                print(f"   Open Price:    {hist.price_open()}")
                print(f"   SL / TP:       {hist.stop_loss()} / {hist.take_profit()}")
                print(
                    f"   Done Time:     {datetime.fromtimestamp(hist.time_done(), tz=UTC)}"
                )
                print("-" * 30)
    except Exception as e:
        print(f"Failed to query history orders: {e}")


def example_08_history_deal() -> None:
    """Demonstrate listing deals using DealInfo."""
    print("\n" + "=" * 100)
    print("--- 8. Fetching Historical Deals ---")
    print("=" * 100)

    try:
        start = datetime(1990, 1, 1, tzinfo=UTC)
        end = datetime.now(UTC)
        broker = get_broker_module()
        deals = broker.get_history_deal_info(date_from=start, date_to=end) or ()
        print(f"Total deals found: {len(deals)}")

        deal = DealInfo()
        for i, raw_deal in enumerate(deals[:5]):  # Print up to 5 deals
            if deal.select(raw_deal.ticket):
                print(f"{i + 1}. Ticket #{deal.ticket()} {deal.symbol()}")
                print(f"   Type:          {deal.type()} ({deal.type_description()})")
                print(f"   Entry:         {deal.entry()} ({deal.entry_description()})")
                print(f"   Price:         {deal.price()}")
                print(f"   Volume:        {deal.volume()}")
                print(f"   Profit:        ${deal.profit():.2f}")
                print(f"   Commission:    ${deal.commission():.2f}")
                print(f"   Swap:          ${deal.swap():.2f}")
                print(f"   Comment:       {deal.comment()}")
                print("-" * 30)
    except Exception as e:
        print(f"Failed to query history deals: {e}")


def example_09_open_position() -> None:
    """Demonstrate opening a position using generic Trade class."""
    global pos_ticket, buy_price, used_filling_mode
    print("\n" + "=" * 100)
    print(f"--- 9. Opening Position (Buy 0.02 {trading_symbol}) ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    client = get_client()
    used_filling_mode = client.ORDER_FILLING_FOK
    if hasattr(sym, "_data") and sym._data:
        filling_val = getattr(sym._data, "filling_mode", 3)
        if filling_val & 2:  # IOC
            used_filling_mode = client.ORDER_FILLING_IOC
        elif filling_val & 1:  # FOK
            used_filling_mode = client.ORDER_FILLING_FOK

    trade = Trade()
    trade.set_symbol(trading_symbol)
    trade.set_expert_magic_number(99999)
    trade.set_deviation_in_points(20)
    trade.set_order_filling(used_filling_mode)

    try:
        buy_price = sym.ask()
        success = trade.buy(0.02, price=buy_price, comment="Unified Usage Buy")
        if success:
            pos_ticket = trade.result_order()
            print(f"Position opened successfully! Ticket: {pos_ticket}")
            print(f"  Execution Price: {trade.result_price()}")
            print(f"  Deal Ticket:     {trade.result_deal()}")
        else:
            print("Failed to open position.")
            print(f"  Result Code:     {trade.result_retcode()}")
            print(f"  Comment:         {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during buy trade order: {e}")


def example_10_calc_profit_margin() -> None:
    """Demonstrate calculating expected profit and required margin."""
    print("\n" + "=" * 100)
    print("--- 10. Pre-trade Profit and Margin Calculation ---")
    print("=" * 100)

    client = get_client()
    if not client.is_connected():
        print("Client is not connected.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    try:
        # 1. Calculate margin
        margin = client.order_calc_margin(
            client.ORDER_TYPE_BUY, trading_symbol, 0.02, sym.ask()
        )
        if margin is not None:
            print(f"Required Margin for Buy 0.02 {trading_symbol}: ${margin:.2f}")
        else:
            print(f"Failed to calculate margin. Error: {client.last_error()}")

        # 2. Calculate profit
        pip_val = sym.point() * 10
        target_price = round(sym.ask() + (100 * pip_val), sym.digits())
        profit = client.order_calc_profit(
            client.ORDER_TYPE_BUY, trading_symbol, 0.02, sym.ask(), target_price
        )
        if profit is not None:
            print(
                f"Expected Profit for Buy 0.02 {trading_symbol} (+100 pips): ${profit:.2f}"
            )
        else:
            print(f"Failed to calculate profit. Error: {client.last_error()}")
    except Exception as e:
        print(f"Exception during calculation: {e}")


def example_11_modify_position() -> None:
    """Demonstrate modifying the Stop Loss / Take Profit of an active position."""
    print("\n" + "=" * 100)
    print("--- 11. Modifying Active Position SL/TP ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping modification.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        sl = round(buy_price - 1000 * pip_val, sym.digits())
        tp = round(buy_price + 1000 * pip_val, sym.digits())

        trade = Trade()
        success = trade.position_modify(pos_ticket, sl=sl, tp=tp)
        if success:
            print(f"Position SL/TP modified successfully. SL: {sl}, TP: {tp}")
        else:
            print(f"Failed to modify position. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during position modification: {e}")


def example_12_close_partial_position() -> None:
    """Demonstrate partial close of an active position (Closing 0.01 lot)."""
    print("\n" + "=" * 100)
    print("--- 12. Partial Closing Active Position (0.01 lot) ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping partial close.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        trade = Trade()
        trade.set_order_filling(used_filling_mode)
        # cTrader closed deals need sell type close for buys
        client = get_client()
        request = {
            "action": client.TRADE_ACTION_DEAL,
            "symbol": trading_symbol,
            "volume": 0.01,
            "type": client.ORDER_TYPE_SELL,
            "position": pos_ticket,
            "price": sym.bid(),
            "deviation": 20,
            "magic": 99999,
            "comment": "Partial Close",
            "type_time": client.ORDER_TIME_GTC,
            "type_filling": used_filling_mode,
        }
        success = trade._send_request(request)
        if success:
            print(f"Partial close executed! Deal Ticket: {trade.result_deal()}")
        else:
            print(f"Failed partial close. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during partial close: {e}")


def example_13_close_position() -> None:
    """Demonstrate closing the remaining active position fully."""
    print("\n" + "=" * 100)
    print("--- 13. Closing Remaining Position Fully ---")
    print("=" * 100)

    if pos_ticket == 0:
        print("No active position from Example 9. Skipping close.")
        return

    time.sleep(1)

    try:
        trade = Trade()
        trade.set_order_filling(used_filling_mode)
        success = trade.position_close(pos_ticket)
        if success:
            print(
                f"Remaining position closed fully! Deal Ticket: {trade.result_deal()}"
            )
        else:
            print(f"Failed to close position. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception during position close: {e}")


def example_14_pending_orders() -> None:
    """Demonstrate placing a Buy Limit pending order."""
    global ord_ticket, limit_price
    print("\n" + "=" * 100)
    print("--- 14. Placing Pending Order (Buy Limit) ---")
    print("=" * 100)

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        limit_price = round(sym.bid() - 200 * pip_val, sym.digits())

        trade = Trade()
        trade.set_symbol(trading_symbol)
        trade.set_order_filling(used_filling_mode)

        success = trade.buy_limit(
            0.01, price=limit_price, comment="Unified Pending Limit"
        )
        if success:
            ord_ticket = trade.result_order()
            print(f"Pending Buy Limit placed successfully! Ticket: {ord_ticket}")
        else:
            print(f"Failed to place pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception placing pending order: {e}")


def example_15_modify_pending_orders() -> None:
    """Demonstrate modifying a placed pending order."""
    print("\n" + "=" * 100)
    print("--- 15. Modifying Pending Order ---")
    print("=" * 100)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping modification.")
        return

    sym = SymbolInfo(trading_symbol)
    if not sym.refresh():
        print(f"Failed to fetch symbol info for {trading_symbol}")
        return

    time.sleep(1)

    try:
        pip_val = sym.point() * 10
        new_limit_price = round(limit_price - 50 * pip_val, sym.digits())

        trade = Trade()
        success = trade.order_modify(ord_ticket, price=new_limit_price, sl=0.0, tp=0.0)
        if success:
            print(f"Pending order modified successfully! New Price: {new_limit_price}")
        else:
            print(f"Failed to modify pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception modifying pending order: {e}")


def example_16_delete_pending_orders() -> None:
    """Demonstrate deleting / cancelling a pending order."""
    print("\n" + "=" * 100)
    print("--- 16. Deleting/Cancelling Pending Order ---")
    print("=" * 100)

    if ord_ticket == 0:
        print("No active pending order from Example 14. Skipping deletion.")
        return

    time.sleep(1)

    try:
        trade = Trade()
        success = trade.order_delete(ord_ticket)
        if success:
            print(f"Pending order deleted successfully! Ticket: {ord_ticket}")
        else:
            print(f"Failed to delete pending order. Comment: {trade.result_comment()}")
    except Exception as e:
        print(f"Exception deleting pending order: {e}")


def example_17_shutdown() -> None:
    """Demonstrate shutting down connection to active broker."""
    print("\n" + "=" * 100)
    print(f"--- 17. Shutting down connection to {settings.active_broker.upper()} ---")
    print("=" * 100)

    client = get_client()
    try:
        if hasattr(client, "shutdown"):
            client.shutdown()
        else:
            client.disconnect()
        print("Broker connection shut down successfully.")
    except Exception as e:
        print(f"Exception during shutdown: {e}")


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
