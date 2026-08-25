"""Tests for squeeze_breakout.py — SqueezeBreakoutStrategy.

Previously had zero test coverage of any kind. Added per trading-strategy-sdk#1's progress
note before the same Extract-Method refactor already applied to the other 6 strategies
(ema_crossover/opening_range_breakout/rsi_mean_reversion/vwap_reversion/dpo_mean_reversion/
linreg_trend) is applied here -- completes the 7/7 series.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from quantindicators.polars_store import PolarsStore
from trading_types.schemas import CandleEvent, InstrumentType, Side

from trading_strategy_sdk.squeeze_breakout import SqueezeBreakoutStrategy

BASE_TS = datetime(2025, 1, 6, 4, 15, tzinfo=UTC)  # 09:45 IST
INFY = "INFY"
EQUITY = InstrumentType.EQUITY


def _candle(
    close: float,
    offset_minutes: int,
    *,
    symbol: str = INFY,
    interval: str = "15min",
    high: float | None = None,
    low: float | None = None,
    volume: int = 1000,
) -> CandleEvent:
    return CandleEvent(
        symbol=symbol,
        instrument_type=EQUITY,
        interval=interval,
        open=close,
        high=high if high is not None else close,
        low=low if low is not None else close,
        close=close,
        volume=volume,
        timestamp=BASE_TS + timedelta(minutes=offset_minutes),
        tick_log_id=0,
    )


class _Harness:
    """Feed CandleEvents through a strategy with a PolarsStore, like AlgoRegistry does."""

    def __init__(self, strategy: SqueezeBreakoutStrategy) -> None:
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
async def test_squeeze_buy_signal_on_breakout_up() -> None:
    strat = SqueezeBreakoutStrategy(
        period=20, bb_k=2.0, kc_k=1.5, squeeze_lookback=5, atr_period=14, atr_multiplier=1.5
    )
    h = _Harness(strat)
    i = 0
    # Perfectly flat price -> std=0, ATR=0 -> squeeze_on=True (0 <= 0), momentum ~0.
    for _ in range(25):
        await h.feed(_candle(100.0, offset_minutes=i))
        i += 1
    # Sharp breakout up, within squeeze_lookback bars of the last squeeze.
    signals = []
    for step in range(5):
        sig = await h.feed(_candle(100.0 + (step + 1) * 5.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.BUY for s in signals), "Expected a BUY signal on squeeze breakout up"


@pytest.mark.asyncio
async def test_squeeze_sell_signal_on_breakout_down() -> None:
    strat = SqueezeBreakoutStrategy(
        period=20, bb_k=2.0, kc_k=1.5, squeeze_lookback=5, atr_period=14, atr_multiplier=1.5
    )
    h = _Harness(strat)
    i = 0
    # Perfectly flat price -> squeeze_on=True, momentum ~0.
    for _ in range(25):
        await h.feed(_candle(100.0, offset_minutes=i))
        i += 1
    # Sharp breakout down, within squeeze_lookback bars of the last squeeze.
    signals = []
    for step in range(5):
        sig = await h.feed(_candle(100.0 - (step + 1) * 5.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.SELL for s in signals), (
        "Expected a SELL signal on squeeze breakout down"
    )


@pytest.mark.asyncio
async def test_squeeze_no_signal_on_insufficient_data() -> None:
    strat = SqueezeBreakoutStrategy()
    h = _Harness(strat)
    sig = await h.feed(_candle(100.0, 0))
    assert sig is None


def test_squeeze_strategy_id() -> None:
    assert SqueezeBreakoutStrategy().id == "squeeze_breakout"
