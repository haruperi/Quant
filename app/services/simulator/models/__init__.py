"""Simulator model public facade.

Exports approved simulator configuration, tick, spread, slippage, liquidity,
fee, swap, and margin primitives. Importing this module has no side effects.
"""

from app.services.simulator.models.fee import CommissionModel
from app.services.simulator.models.liquidity import (
    FixedLiquidityModel,
    LiquidityFill,
    OrderBookLevel,
    OrderBookLiquidityModel,
)
from app.services.simulator.models.margin import MarginModel
from app.services.simulator.models.slippage import (
    FixedSlippageModel,
    SlippageResult,
    VolatilitySlippageModel,
    VolumeSlippageModel,
)
from app.services.simulator.models.spread import FixedSpreadModel, VariableSpreadModel
from app.services.simulator.models.swap import SwapModel
from app.services.simulator.models.tick import (
    SimulatorActorContext,
    SimulatorBacktestRequestV1,
    SimulatorSymbolSpec,
    SimulatorTick,
)

__all__ = [
    "CommissionModel",
    "FixedLiquidityModel",
    "FixedSlippageModel",
    "FixedSpreadModel",
    "LiquidityFill",
    "MarginModel",
    "OrderBookLevel",
    "OrderBookLiquidityModel",
    "SimulatorActorContext",
    "SimulatorBacktestRequestV1",
    "SimulatorSymbolSpec",
    "SimulatorTick",
    "SlippageResult",
    "SwapModel",
    "VariableSpreadModel",
    "VolatilitySlippageModel",
    "VolumeSlippageModel",
]
