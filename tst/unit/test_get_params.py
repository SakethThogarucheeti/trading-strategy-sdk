"""get_params() must echo the constructor kwargs for every strategy.

Regression test: RsiMeanReversion/LinregTrend/DpoMeanReversion/SqueezeBreakout
all inherited the base class's no-op get_params() (returns {}), silently
hiding live strategy params from anything that reads them back (e.g. a
dashboard persisting config via seed_algo_config).
"""

from __future__ import annotations

from trading_strategy_sdk.dpo_mean_reversion import DpoMeanReversionStrategy
from trading_strategy_sdk.ema_crossover import EmaCrossoverStrategy
from trading_strategy_sdk.linreg_trend import LinRegTrendStrategy
from trading_strategy_sdk.rsi_mean_reversion import RsiMeanReversionStrategy
from trading_strategy_sdk.squeeze_breakout import SqueezeBreakoutStrategy


def test_ema_crossover_get_params() -> None:
    s = EmaCrossoverStrategy(fast=12, slow=26, atr_period=14, atr_multiplier=2.0)
    assert s.get_params() == {"fast": 12, "slow": 26, "atr_period": 14, "atr_multiplier": 2.0}


def test_rsi_mean_reversion_get_params() -> None:
    s = RsiMeanReversionStrategy(
        rsi_period=14, oversold=35, overbought=70, atr_period=14, atr_multiplier=1.0
    )
    assert s.get_params() == {
        "rsi_period": 14,
        "oversold": 35,
        "overbought": 70,
        "atr_period": 14,
        "atr_multiplier": 1.0,
    }


def test_linreg_trend_get_params() -> None:
    s = LinRegTrendStrategy(period=20, entry_threshold=0.1, atr_period=14, atr_multiplier=1.5)
    assert s.get_params() == {
        "period": 20,
        "entry_threshold": 0.1,
        "atr_period": 14,
        "atr_multiplier": 1.5,
    }


def test_dpo_mean_reversion_get_params() -> None:
    s = DpoMeanReversionStrategy(period=20, dpo_atr_mult=1.2, atr_period=14, atr_multiplier=1.5)
    assert s.get_params() == {
        "period": 20,
        "dpo_atr_mult": 1.2,
        "atr_period": 14,
        "atr_multiplier": 1.5,
    }


def test_squeeze_breakout_get_params() -> None:
    s = SqueezeBreakoutStrategy(
        period=20, bb_k=2.0, kc_k=1.5, squeeze_lookback=5, atr_period=14, atr_multiplier=1.5
    )
    assert s.get_params() == {
        "period": 20,
        "bb_k": 2.0,
        "kc_k": 1.5,
        "squeeze_lookback": 5,
        "atr_period": 14,
        "atr_multiplier": 1.5,
    }
