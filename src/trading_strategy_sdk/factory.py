from __future__ import annotations

from typing import Any

from trading_types.clock import Clock

from trading_strategy_sdk.base import _REGISTRY, RuntimeContext, Strategy

# Each import below triggers Strategy.__init_subclass__, which self-registers
# the class into base._REGISTRY keyed by its own `alias` -- get_strategy()/
# registered_strategies() read that registry directly rather than hand-
# duplicating each alias string in a separate dict here. This list is still
# what curates which strategies are selectable at all: a class that's never
# imported never registers, same allowlist property as before (see
# trading-strategy-sdk#7).
from trading_strategy_sdk.dpo_mean_reversion import DpoMeanReversionStrategy  # noqa: F401
from trading_strategy_sdk.ema_crossover import EmaCrossoverStrategy  # noqa: F401
from trading_strategy_sdk.linreg_trend import LinRegTrendStrategy  # noqa: F401
from trading_strategy_sdk.opening_range_breakout import OpeningRangeBreakoutStrategy  # noqa: F401
from trading_strategy_sdk.rsi_mean_reversion import RsiMeanReversionStrategy  # noqa: F401
from trading_strategy_sdk.squeeze_breakout import SqueezeBreakoutStrategy  # noqa: F401
from trading_strategy_sdk.vwap_reversion import VwapReversionStrategy  # noqa: F401


def get_strategy(strategy_id: str) -> type[Strategy]:
    try:
        return _REGISTRY[strategy_id]
    except KeyError:
        available = ", ".join(sorted(_REGISTRY))
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
    return dict(_REGISTRY)
