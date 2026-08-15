from __future__ import annotations

from quantindicators.store import AbstractCandleStore


class IndicatorCacheMixin[IndTuple: tuple[object, ...]]:
    """
    Lazily constructs and caches one indicator tuple per symbol.

    Strategies subclass with the concrete tuple type, call
    ``self._init_indicator_cache()`` in ``__init__``, and implement
    ``_build_indicators``, e.g.::

        class MyStrategy(IndicatorCacheMixin[tuple[EMA, ATR]], Strategy):
            def __init__(self, ...) -> None:
                self._init_indicator_cache()

            def _build_indicators(self, store, symbol, interval):
                return EMA(store, symbol, interval), ATR(store, symbol, interval)
    """

    _store: AbstractCandleStore | None = None

    def _init_indicator_cache(self) -> None:
        self._store = None
        self._inds: dict[str, IndTuple] = {}

    def set_store(self, store: AbstractCandleStore) -> None:
        self._store = store

    def _build_indicators(
        self, store: AbstractCandleStore, symbol: str, interval: str
    ) -> IndTuple:
        raise NotImplementedError

    def _get_inds(self, symbol: str, interval: str) -> IndTuple:
        if symbol not in self._inds:
            assert self._store is not None, "set_store() must be called before on_candle()"
            self._inds[symbol] = self._build_indicators(self._store, symbol, interval)
        return self._inds[symbol]
