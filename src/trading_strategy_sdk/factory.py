from __future__ import annotations

from typing import Any

from trading_types.clock import Clock

from trading_strategy_sdk.base import RuntimeContext, Strategy
from trading_strategy_sdk.dpo_mean_reversion import DpoMeanReversionStrategy
from trading_strategy_sdk.ema_crossover import EmaCrossoverStrategy
from trading_strategy_sdk.linreg_trend import LinRegTrendStrategy
from trading_strategy_sdk.opening_range_breakout import OpeningRangeBreakoutStrategy
from trading_strategy_sdk.rsi_mean_reversion import RsiMeanReversionStrategy
from trading_strategy_sdk.squeeze_breakout import SqueezeBreakoutStrategy
from trading_strategy_sdk.vwap_reversion import VwapReversionStrategy

_STRATEGIES: dict[str, type[Strategy]] = {
    "ema_crossover": EmaCrossoverStrategy,
    "rsi_mean_reversion": RsiMeanReversionStrategy,
    "opening_range_breakout": OpeningRangeBreakoutStrategy,
    "vwap_reversion": VwapReversionStrategy,
    "linreg_trend": LinRegTrendStrategy,
    "dpo_mean_reversion": DpoMeanReversionStrategy,
    "squeeze_breakout": SqueezeBreakoutStrategy,
}


def get_strategy(strategy_id: str) -> type[Strategy]:
    try:
        return _STRATEGIES[strategy_id]
    except KeyError:
        available = ", ".join(sorted(_STRATEGIES))
        raise ValueError(f"Unknown strategy {strategy_id!r}. Available: {available}.") from None


def create_strategy(
    strategy_id: str,
    params: dict[str, Any] | None = None,
    clock: Clock | None = None,
) -> Strategy:
    cls = get_strategy(strategy_id)
    kwargs = dict(params or {})
    strategy = cls(**kwargs)
    if clock is not None:
        strategy.set_runtime_context(RuntimeContext(clock=clock))
    return strategy


def registered_strategies() -> dict[str, type[Strategy]]:
    return dict(_STRATEGIES)
