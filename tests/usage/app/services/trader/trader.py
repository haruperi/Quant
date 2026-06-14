# ruff: noqa: E501, PLR0915, PLR0912, BLE001, C901, E402
"""Usage example for the generic Trade classes."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parents[5])
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


def run_trader_usage_demo() -> None:
    """Run step-by-step generic trade classes operations."""
    print("=" * 100)
    print(
        f"Starting Generic Trade Classes Demo. Active Broker: {settings.active_broker}"
    )
    print("=" * 100)

    # 1. Terminal Info
    print("\n--- 1. Fetching Terminal Info ---")
    term = TerminalInfo()
    try:
        print(f"Name:             {term.name()}")
        print(f"Company:          {term.company()}")
        print(f"Build:            {term.build()}")
        print(f"Language:         {term.language()}")
        print(f"Connected:        {term.connected()}")
        print(f"Trade Allowed:    {term.trade_allowed()}")
        print(f"Ping Last (us):   {term.ping_last()}")
    except Exception as e:
        print(f"Failed to fetch terminal info: {e}")

    # 2. Account Info
    print("\n--- 2. Fetching Account Info ---")
    acc = AccountInfo()
    try:
        print(f"Login:            {acc.login()}")
        print(f"Name:             {acc.name()}")
        print(f"Server:           {acc.server()}")
        print(f"Currency:         {acc.currency()}")
        print(f"Balance:          {acc.balance():.2f} {acc.currency()}")
        print(f"Equity:           {acc.equity():.2f} {acc.currency()}")
        print(f"Free Margin:      {acc.free_margin():.2f} {acc.currency()}")
        print(f"Leverage:         1:{acc.leverage()}")
    except Exception as e:
        print(f"Failed to fetch account info: {e}")

    # 3. Symbol Info
    symbol_name = "EURUSD"
    print(f"\n--- 3. Fetching Symbol Info for {symbol_name} ---")
    sym = SymbolInfo(symbol_name)
    try:
        if sym.refresh():
            print(f"Symbol:           {sym.name()}")
            print(f"Digits:           {sym.digits()}")
            print(f"Point:            {sym.point()}")
            print(f"Bid:              {sym.bid()}")
            print(f"Ask:              {sym.ask()}")
            print(f"Spread:           {sym.spread()} points")
            print(f"Min Volume:       {sym.volume_min()}")
            print(f"Max Volume:       {sym.volume_max()}")
            print(f"Volume Step:      {sym.volume_step()}")
            print(f"Swap Long:        {sym.swap_long()}")
            print(f"Swap Short:       {sym.swap_short()}")
        else:
            print(f"Failed to refresh symbol specifications for {symbol_name}")
    except Exception as e:
        print(f"Failed to fetch symbol info: {e}")

    # 4. Open a Position (Buy 0.01 lot)
    print("\n--- 4. Opening Position (Buy 0.01 lot EURUSD) ---")
    trade = Trade()
    trade.set_symbol(symbol_name)
    trade.set_expert_magic_number(12345)
    trade.set_deviation_in_points(20)

    try:
        success = trade.buy(0.01, comment="Generic Trade Demo Buy")
        if success:
            print("Position opened successfully!")
            print(f"  Result Code:    {trade.result_retcode()}")
            print(f"  Order Ticket:   {trade.result_order()}")
            print(f"  Deal Ticket:    {trade.result_deal()}")
            print(f"  Price:          {trade.result_price()}")
            print(f"  Comment:        {trade.result_comment()}")
        else:
            print("Failed to open position.")
            print(f"  Result Code:    {trade.result_retcode()}")
            print(f"  Comment:        {trade.result_comment()}")
            return  # Skip subsequent steps if buy fails
    except Exception as e:
        print(f"Failed to send trade request: {e}")
        return

    # 5. Position Info
    ticket = trade.result_order()
    print(f"\n--- 5. Fetching Open Position Info (Ticket {ticket}) ---")
    pos = PositionInfo()
    try:
        if pos.select_by_ticket(ticket):
            print(f"Ticket:           {pos.ticket()}")
            print(f"Symbol:           {pos.symbol()}")
            print(f"Type:             {pos.type_description()}")
            print(f"Volume:           {pos.volume()}")
            print(f"Open Price:       {pos.price_open()}")
            print(f"Current Price:    {pos.price_current()}")
            print(f"Profit:           ${pos.profit():.2f}")
            print(f"SL / TP:          {pos.stop_loss()} / {pos.take_profit()}")
        else:
            print(f"Failed to select open position by ticket {ticket}")
    except Exception as e:
        print(f"Failed to select position: {e}")

    # 6. Modify Position (Set SL/TP)
    print("\n--- 6. Modifying Position SL/TP ---")
    try:
        # Move SL 100 pips down and TP 100 pips up
        pip_val = sym.point() * 10
        open_price = pos.price_open()
        sl = round(open_price - 100 * pip_val, sym.digits())
        tp = round(open_price + 100 * pip_val, sym.digits())

        success = trade.position_modify(ticket, sl=sl, tp=tp)
        if success:
            print(f"Position modified successfully! SL set to {sl}, TP set to {tp}")
        else:
            print(f"Failed to modify position: {trade.result_comment()}")
    except Exception as e:
        print(f"Failed to modify position: {e}")

    # 7. Place Pending Order (Buy Limit)
    print("\n--- 7. Placing Pending Order (Buy Limit) ---")
    ord_ticket = 0
    try:
        # Place Buy Limit 200 pips below current bid price
        limit_price = round(sym.bid() - 200 * pip_val, sym.digits())
        success = trade.buy_limit(
            0.01, price=limit_price, comment="Generic Trade Demo BuyLimit"
        )
        if success:
            ord_ticket = trade.result_order()
            print(f"Buy Limit order placed successfully! Ticket: {ord_ticket}")
        else:
            print(f"Failed to place Buy Limit order: {trade.result_comment()}")
    except Exception as e:
        print(f"Failed to place limit order: {e}")

    # 8. Pending Order Info
    if ord_ticket > 0:
        print(f"\n--- 8. Fetching Pending Order Info (Ticket {ord_ticket}) ---")
        ord_info = OrderInfo(ord_ticket)
        try:
            print(f"Ticket:           {ord_info.ticket()}")
            print(f"Symbol:           {ord_info.symbol()}")
            print(f"Type:             {ord_info.type_description()}")
            print(f"Limit Price:      {ord_info.price_open()}")
            print(f"State:            {ord_info.state_description()}")
        except Exception as e:
            print(f"Failed to fetch pending order info: {e}")

        # 9. Modify Pending Order
        print("\n--- 9. Modifying Pending Order ---")
        try:
            new_limit_price = round(limit_price - 50 * pip_val, sym.digits())
            success = trade.order_modify(
                ord_ticket, price=new_limit_price, sl=0.0, tp=0.0
            )
            if success:
                print(f"Pending order modified! New Price: {new_limit_price}")
            else:
                print(f"Failed to modify pending order: {trade.result_comment()}")
        except Exception as e:
            print(f"Failed to modify pending order: {e}")

        # 10. Delete Pending Order
        print("\n--- 10. Deleting/Cancelling Pending Order ---")
        try:
            success = trade.order_delete(ord_ticket)
            if success:
                print("Pending order cancelled successfully.")
            else:
                print(f"Failed to cancel pending order: {trade.result_comment()}")
        except Exception as e:
            print(f"Failed to cancel pending order: {e}")

    # 11. Close Open Position
    print(f"\n--- 11. Closing Open Position (Ticket {ticket}) ---")
    try:
        success = trade.position_close(ticket)
        if success:
            print("Position closed successfully.")
        else:
            print(f"Failed to close position: {trade.result_comment()}")
    except Exception as e:
        print(f"Failed to close position: {e}")

    # 12. History Order Info & Deal Info
    print("\n--- 12. Fetching History and Deals ---")
    hist_ord = HistoryOrderInfo()
    try:
        if hist_ord.select(ticket):
            print(f"Historical Order Ticket:   {hist_ord.ticket()}")
            print(f"Order State:              {hist_ord.state_description()}")
            print(
                f"Order Done Time:          {datetime.fromtimestamp(hist_ord.time_done(), tz=UTC)}"
            )
    except Exception as e:
        print(f"Failed to select historical order: {e}")

    deal = DealInfo()
    deal_ticket = trade.result_deal()
    if deal_ticket > 0:
        try:
            if deal.select(deal_ticket):
                print(f"Historical Deal Ticket:    {deal.ticket()}")
                print(f"Deal Profit:               ${deal.profit():.2f}")
                print(f"Deal Commission:           ${deal.commission():.2f}")
                print(f"Deal Comment:              {deal.comment()}")
        except Exception as e:
            print(f"Failed to select deal: {e}")


if __name__ == "__main__":
    run_trader_usage_demo()
