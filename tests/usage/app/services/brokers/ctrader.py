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
