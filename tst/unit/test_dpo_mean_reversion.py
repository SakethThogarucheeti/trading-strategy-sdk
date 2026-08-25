"""Tests for dpo_mean_reversion.py — DpoMeanReversionStrategy.

Prior coverage for this strategy was limited to get_params() (see test_get_params.py) —
zero coverage of on_candle's BUY/SELL signal path. Added per trading-strategy-sdk#1's
progress note before the same Extract-Method refactor already applied to
ema_crossover/opening_range_breakout/rsi_mean_reversion/vwap_reversion is applied here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from quantindicators.polars_store import PolarsStore
from trading_types.schemas import CandleEvent, InstrumentType, Side

from trading_strategy_sdk.dpo_mean_reversion import DpoMeanReversionStrategy

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

    def __init__(self, strategy: DpoMeanReversionStrategy) -> None:
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
async def test_dpo_buy_signal_on_oversold_turn_up() -> None:
    strat = DpoMeanReversionStrategy(period=20, dpo_atr_mult=1.0, atr_period=14, atr_multiplier=1.5)
    h = _Harness(strat)
    i = 0
    # Falling phase, long enough to build a deeply negative DPO (needs period+shift=31
    # bars before the first non-None reading) and a nonzero ATR.
    for step in range(45):
        await h.feed(_candle(300.0 - step * 3.0, offset_minutes=i))
        i += 1
    # Turning-up phase: small upticks while the trailing window is still dominated by
    # the decline, so DPO stays below -threshold while rising bar-over-bar.
    signals = []
    for step in range(20):
        sig = await h.feed(_candle(165.0 + step * 1.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.BUY for s in signals), "Expected a BUY signal on oversold turn-up"


@pytest.mark.asyncio
async def test_dpo_sell_signal_on_overbought_turn_down() -> None:
    strat = DpoMeanReversionStrategy(period=20, dpo_atr_mult=1.0, atr_period=14, atr_multiplier=1.5)
    h = _Harness(strat)
    i = 0
    # Rising phase, long enough to build a deeply positive DPO.
    for step in range(45):
        await h.feed(_candle(100.0 + step * 3.0, offset_minutes=i))
        i += 1
    # Turning-down phase: small downticks while the trailing window is still dominated
    # by the rise, so DPO stays above +threshold while falling bar-over-bar.
    signals = []
    for step in range(20):
        sig = await h.feed(_candle(235.0 - step * 1.0, offset_minutes=i))
        i += 1
        if sig is not None:
            signals.append(sig)
    assert any(s.side == Side.SELL for s in signals), (
        "Expected a SELL signal on overbought turn-down"
    )


@pytest.mark.asyncio
async def test_dpo_no_signal_on_insufficient_data() -> None:
    strat = DpoMeanReversionStrategy()
    h = _Harness(strat)
    sig = await h.feed(_candle(100.0, 0))
    assert sig is None


def test_dpo_strategy_id() -> None:
    assert DpoMeanReversionStrategy().id == "dpo_mean_reversion"
