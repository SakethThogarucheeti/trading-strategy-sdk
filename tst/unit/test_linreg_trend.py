"""Tests for linreg_trend.py — LinRegTrendStrategy.

Previously had zero test coverage of any kind (not even get_params). Added per
trading-strategy-sdk#1's progress note before the same Extract-Method refactor already
applied to ema_crossover/opening_range_breakout/rsi_mean_reversion/vwap_reversion/
dpo_mean_reversion is applied here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from quantindicators.polars_store import PolarsStore
from trading_types.schemas import CandleEvent, InstrumentType, Side

from trading_strategy_sdk.linreg_trend import LinRegTrendStrategy

BASE_TS = datetime(2025, 1, 6, 4, 15, tzinfo=UTC)  # 09:45 IST
INFY = "INFY"
EQUITY = InstrumentType.EQUITY


def _candle(
    close: float,
    offset_minutes: int,
    *,
    symbol: str = INFY,
    interval: str = "15min",
    volume: int = 1000,
) -> CandleEvent:
    return CandleEvent(
        symbol=symbol,
        instrument_type=EQUITY,
        interval=interval,
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=volume,
        timestamp=BASE_TS + timedelta(minutes=offset_minutes),
        tick_log_id=0,
    )


class _Harness:
    """Feed CandleEvents through a strategy with a PolarsStore, like AlgoRegistry does."""

    def __init__(self, strategy: LinRegTrendStrategy) -> None:
        self._strategy = strategy
        self._store = PolarsStore()
        strategy.set_store(self._store)

    async def feed(self, candle: CandleEvent):
        self._store.push(
            candle.symbol,
            candle.interval,
            {
                "symbol": candle.symbol,
                "interval": candle.interval,
                "ts": candle.timestamp,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            },
        )
        return await self._strategy.on_candle(candle.symbol, EQUITY, candle)


@pytest.mark.asyncio
async def test_linreg_buy_signal_on_downtrend_to_uptrend() -> None:
    strat = LinRegTrendStrategy(period=20, entry_threshold=0.0, atr_period=14, atr_multiplier=1.5)
    h = _Harness(strat)
    i = 0
    # Downtrend phase: builds a negative slope (needs >= period=20 bars for the first
    # non-None reading, and a second reading for prev_slope to be set).
    for step in range(30):
        await h.feed(_candle(200.0 - step * 3.0, offset_minutes=i))
        i += 1
    # Uptrend phase: slope crosses above the (zero) entry threshold.
    signals = []
    for step in range(30):
        sig = await h.feed(_candle(110.0 + step * 4.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.BUY for s in signals), "Expected a BUY signal on trend turning up"


@pytest.mark.asyncio
async def test_linreg_sell_signal_on_uptrend_to_downtrend() -> None:
    strat = LinRegTrendStrategy(period=20, entry_threshold=0.0, atr_period=14, atr_multiplier=1.5)
    h = _Harness(strat)
    i = 0
    # Uptrend phase: builds a positive slope.
    for step in range(30):
        await h.feed(_candle(100.0 + step * 3.0, offset_minutes=i))
        i += 1
    # Downtrend phase: slope crosses below the (zero) entry threshold.
    signals = []
    for step in range(30):
        sig = await h.feed(_candle(190.0 - step * 4.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.SELL for s in signals), (
        "Expected a SELL signal on trend turning down"
    )


@pytest.mark.asyncio
async def test_linreg_no_signal_on_insufficient_data() -> None:
    strat = LinRegTrendStrategy()
    h = _Harness(strat)
    sig = await h.feed(_candle(100.0, 0))
    assert sig is None


def test_linreg_strategy_id() -> None:
    assert LinRegTrendStrategy().id == "linreg_trend"
