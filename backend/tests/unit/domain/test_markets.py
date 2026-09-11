from screener.domain.markets import DEFAULT_MARKET_ID, MARKETS, is_known_market


class TestMarkets:
    def test_default_market_is_first_and_present(self):
        assert MARKETS[0].id == DEFAULT_MARKET_ID

    def test_all_market_ids_are_unique(self):
        ids = [m.id for m in MARKETS]
        assert len(ids) == len(set(ids))

    def test_includes_all_four_real_markets(self):
        ids = {m.id for m in MARKETS}
        assert ids == {"default", "sp500", "nasdaq100", "nse500", "bse500"}

    def test_is_known_market_true_for_real_ids(self):
        assert is_known_market("sp500")
        assert is_known_market("default")

    def test_is_known_market_false_for_unknown_id(self):
        assert not is_known_market("dow30")
