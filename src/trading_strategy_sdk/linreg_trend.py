"""Linear Regression Slope Trend Strategy.

One of the top-performing indicators by mean ICIR (21.0) across 30-bar horizons.
Strategy: trend-following — enter when slope turns positive after negative (BUY),
exit/short when slope turns negative after positive (SELL).
"""

from __future__ import annotations

import logging
from typing import TypedDict, cast

from quantindicators.library.atr import ATR
from quantindicators.library.linreg_slope import LinearRegressionSlope
from quantindicators.store import AbstractCandleStore
from trading_types.schemas import CandleEvent, InstrumentType, Side

from trading_strategy_sdk.base import Signal, Strategy
from trading_strategy_sdk.indicator_cache import IndicatorCacheMixin


class _State(TypedDict, total=False):
    prev_slope: dict[str, float | None]
    last_slope: float | None
    last_atr: float | None

logger = logging.getLogger(__name__)


class LinRegTrendStrategy(IndicatorCacheMixin[tuple[LinearRegressionSlope, ATR]], Strategy):
    """
    Trend-following via Linear Regression Slope.

    BUY  when slope crosses above *entry_threshold* (trend turning up).
    SELL when slope crosses below *-entry_threshold* (trend turning down).
    Stop distance = ATR × atr_multiplier.
    """

    alias = "linreg_trend"

    def __init__(
        self,
        period: int = 20,
        entry_threshold: float = 0.0,
        atr_period: int = 14,
        atr_multiplier: float = 1.5,
    ) -> None:
        self._period = period
        self._entry_threshold = entry_threshold
        self._atr_period = atr_period
        self._atr_multiplier = atr_multiplier
        self._init_indicator_cache()
        self._prev_slope: dict[str, float | None] = {}
        self._last_slope: float | None = None
        self._last_atr: float | None = None

    def _build_indicators(
        self, store: AbstractCandleStore, symbol: str, interval: str
    ) -> tuple[LinearRegressionSlope, ATR]:
        return (
            LinearRegressionSlope(store, symbol, interval),
            ATR(store, symbol, interval),
        )

    def get_params(self) -> dict[str, object]:
        return {
            "period": self._period,
            "entry_threshold": self._entry_threshold,
            "atr_period": self._atr_period,
            "atr_multiplier": self._atr_multiplier,
        }

    def get_state(self) -> dict[str, object]:
        return {
            f"linreg_slope_{self._period}": round(self._last_slope, 4)
            if self._last_slope is not None
            else None,
            f"atr_{self._atr_period}": round(self._last_atr, 4)
            if self._last_atr is not None
            else None,
            "entry_threshold": self._entry_threshold,
        }

    def rolling_state(self) -> dict[str, object]:
        return {
            "prev_slope": self._prev_slope,
            "last_slope": self._last_slope,
            "last_atr": self._last_atr,
        }

    async def restore_from_state(self, state: dict[str, object]) -> bool:
        try:
            s = cast(_State, state)
            self._prev_slope = dict(s["prev_slope"])
            self._last_slope = s.get("last_slope")
            self._last_atr = s.get("last_atr")
            return True
        except (KeyError, TypeError, AttributeError):
            return False

    async def on_candle(
        self,
        symbol: str,
        instrument_type: InstrumentType,
        candle: CandleEvent,
    ) -> Signal | None:
        slope_ind, atr_ind = self._get_inds(symbol, candle.interval)
        slope = await slope_ind.compute(LinearRegressionSlope.Parameters(period=self._period))
        atr = await atr_ind.compute(ATR.Parameters(period=self._atr_period))

        self._last_slope = slope
        self._last_atr = atr

        self.chart("oscillators", f"linreg_slope_{self._period}", slope, candle.timestamp)
        self.chart("oscillators", f"atr_{self._atr_period}", atr, candle.timestamp)

        prev_slope = self._prev_slope.get(symbol)
        self._prev_slope[symbol] = slope

        if slope is None or atr is None or atr <= 0 or prev_slope is None:
            return None

        stop_distance = self._atr_multiplier * atr

        if prev_slope <= self._entry_threshold and slope > self._entry_threshold:
            return self._build_trend_signal(
                Side.BUY, symbol, instrument_type, prev_slope, slope, stop_distance, candle
            )

        if prev_slope >= -self._entry_threshold and slope < -self._entry_threshold:
            return self._build_trend_signal(
                Side.SELL, symbol, instrument_type, prev_slope, slope, stop_distance, candle
            )

        return None

    def _build_trend_signal(
        self,
        side: Side,
        symbol: str,
        instrument_type: InstrumentType,
        prev_slope: float,
        slope: float,
        stop_distance: float,
        candle: CandleEvent,
    ) -> Signal:
        if side == Side.BUY:
            logger.info(
                "LinRegTrend[%s]: BUY  slope=%.4f→%.4f stop=%.4f",
                symbol, prev_slope, slope, stop_distance,
            )
        else:
            logger.info(
                "LinRegTrend[%s]: SELL slope=%.4f→%.4f stop=%.4f",
                symbol, prev_slope, slope, stop_distance,
            )
        return self._entry_signal(symbol, instrument_type, side, stop_distance, candle)
