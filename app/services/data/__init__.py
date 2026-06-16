"""Market Data Service.

Provides contract-driven historical, real-time, local, synthetic, and broker
market data interfaces and orchestration.
"""

from app.services.data.gateway import (
    get_data,
    get_data_availability,
    get_symbol_metadata,
    list_symbols,
)
from app.services.data.scheduler import (
    create_data_update_job,
    get_data_update_job_status,
    get_feed_status,
    run_data_update_job_once,
    start_data_update_job,
    stop_data_update_job,
)
from app.services.data.storage import (
    clear_data_cache,
    load_local_dataset,
    save_market_data,
)
from app.services.data.transforms import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    label_market_data,
    resample_ohlcv,
)
from app.services.data.validation import (
    get_market_hours,
    get_trading_sessions,
)

__all__ = [
    "aggregate_ticks_to_bars",
    "align_multitimeframe_data",
    "clear_data_cache",
    "create_data_update_job",
    "generate_synthetic_bars",
    "generate_synthetic_ticks",
    "get_data",
    "get_data_availability",
    "get_data_update_job_status",
    "get_feed_status",
    "get_market_hours",
    "get_symbol_metadata",
    "get_trading_sessions",
    "label_market_data",
    "list_symbols",
    "load_local_dataset",
    "resample_ohlcv",
    "run_data_update_job_once",
    "save_market_data",
    "start_data_update_job",
    "stop_data_update_job",
]
