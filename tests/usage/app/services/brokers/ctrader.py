"""Usage example for CTraderClient Open API connection."""

import sys
import time
from pathlib import Path

# Add the project root to sys.path to allow direct execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[5])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.brokers.ctrader import get_ctrader_client  # noqa: E402


def run_ctrader_demo() -> None:
    """Run cTrader connection and authorization handshake demo."""
    print("\n" + "=" * 100)
    print("--- cTrader Open API Connection Handshake Demo ---")
    print("=" * 100)

    client = get_ctrader_client()

    print(
        f"Initial Client State: Connected={client.is_connected()}, "
        f"AppAuth={client.is_app_authenticated()}, "
        f"AccAuth={client.is_account_authorized()}"
    )

    try:
        print("Attempting to connect and perform auth handshake...")
        success = client.connect()
        if success:
            print("cTrader Client successfully connected and authenticated!")
            print(f"Connected:             {client.is_connected()}")
            print(f"App Authenticated:     {client.is_app_authenticated()}")
            print(f"Account Authorized:    {client.is_account_authorized()}")
            print(f"Authorized Account ID: {client.account_id}")
            print()

            trader = client.trader_info
            if trader is not None:
                asset_map = {
                    1: "USD",
                    2: "EUR",
                    3: "GBP",
                    4: "JPY",
                    5: "CHF",
                    6: "CAD",
                    7: "AUD",
                    8: "NZD",
                    9: "SGD",
                    10: "HKD",
                    15: "EUR",
                }
                currency = asset_map.get(
                    trader.depositAssetId, f"Asset ID {trader.depositAssetId}"
                )
                leverage = getattr(trader, "maxLeverage", 0)
                leverage_in_cents = getattr(trader, "leverageInCents", None)
                if not leverage and leverage_in_cents is not None:
                    leverage = leverage_in_cents // 100

                print(f"Login:          {trader.traderLogin}")
                print(f"Name:           cTrader Account {trader.ctidTraderAccountId}")
                print(f"Server:         {trader.accountType}")
                print(f"Company:        {trader.brokerName}")
                print(f"Currency:       {currency}")
                print(f"Leverage:       1:{leverage}")
                balance = trader.balance / 100
                print(f"Balance:        {balance:.2f} {currency}")

            # Sleep briefly to allow any incoming messages to be parsed/printed
            time.sleep(2)
        else:
            print("Failed to authenticate cTrader Client.")
    except Exception as e:  # noqa: BLE001
        print(f"Exception during connection handshake: {e}")
    finally:
        print("Shutting down cTrader connection...")
        client.disconnect()
        print("cTrader connection shut down successfully.")
        print(
            f"Final Client State: Connected={client.is_connected()}, "
            f"AppAuth={client.is_app_authenticated()}, "
            f"AccAuth={client.is_account_authorized()}"
        )


if __name__ == "__main__":
    run_ctrader_demo()
