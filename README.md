# trading-strategy-sdk

Strategy-authoring toolkit for the trading platform: the `Strategy` base class, `Signal` result type, `IndicatorCacheMixin`, and the built-in concrete strategies, plus a factory/registry to look a strategy up by name. Used by [trading-platform](https://github.com/SakethThogarucheeti/trading-platform) and reusable standalone (e.g. for backtesting) without any database, broker, or DI dependency.

## Contents

- `trading_strategy_sdk.base` — `Strategy` (ABC), `Signal`, `AlgoInstance`, `AlgoRunConfig`, `RuntimeContext`.
- `trading_strategy_sdk.indicator_cache` — `IndicatorCacheMixin`, shared lazy per-symbol indicator caching for strategies built on `quantindicators`.
- `trading_strategy_sdk.factory` — `get_strategy()`, `create_strategy()`, `registered_strategies()`.
- Concrete strategies: `ema_crossover`, `dpo_mean_reversion`, `linreg_trend`, `opening_range_breakout`, `rsi_mean_reversion`, `squeeze_breakout`, `vwap_reversion`.

No database, broker, or DI dependency — `on_candle()` is a pure function of candle data and internal state.

## Stack

- Python 3.13+, [uv](https://docs.astral.sh/uv/)
- Pydantic, [quantindicators](https://github.com/SakethThogarucheeti/quantindicators), [trading-types](https://github.com/SakethThogarucheeti/trading-types)

## Setup

```bash
uv sync
```

## Testing

```bash
uv run pytest
```

## Adding a new strategy

Subclass `Strategy`, set a unique `alias`, implement `on_candle()`, and register it in `factory.py`'s `_STRATEGIES` dict.
