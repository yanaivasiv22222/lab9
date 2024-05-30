import pytest
from datetime import datetime
from unittest.mock import patch
import json

from .coinbaseloader import CoinbaseLoader, Granularity
from pydantic import BaseModel, validator, Field
from typing import List



sample_pairs_response = json.dumps([
    {"id": "BTC-USD", "base_currency": "BTC", "quote_currency": "USD", "base_min_size": "0.001"},
    {"id": "ETH-USD", "base_currency": "ETH", "quote_currency": "USD", "base_min_size": "0.01"}
])

sample_stats_response = json.dumps({
    "id": "BTC-USD",
    "base_currency": "BTC",
    "quote_currency": "USD",
    "base_min_size": "0.001",
    "quote_increment": "0.01",
    "display_name": "BTC/USD"
})

sample_historical_data_response = json.dumps([
    {"timestamp": 1625097600, "low": 33513.57, "high": 33687.53, "open": 33600.00, "close": 33653.99, "volume": 28.36152462},
    {"timestamp": 1625011200, "low": 33918.64, "high": 33970.96, "open": 33893.76, "close": 33909.51, "volume": 27.52331336}
])



class Pair(BaseModel):
    id: str
    base_currency: str
    quote_currency: str
    base_min_size: str = Field(..., description="Minimum size of base currency")

    @validator("id")
    def id_must_contain_dash(cls, v):
        if "-" not in v:
            raise ValueError("ID must contain a dash (-)")
        return v

class Stat(BaseModel):
    id: str
    base_currency: str
    quote_currency: str
    base_min_size: str
    quote_increment: str
    display_name: str

class HistoricalDataItem(BaseModel):
    timestamp: int
    low: float
    high: float
    open: float
    close: float
    volume: float

class HistoricalData(BaseModel):
    data: List[HistoricalDataItem]

    @validator("data")
    def data_must_contain_at_least_one_item(cls, v):
        if len(v) < 1:
            raise ValueError("Historical data must contain at least one item")
        return v



@pytest.fixture
def coinbase_loader():
    return CoinbaseLoader()

@patch.object(CoinbaseLoader, '_get_req')
def test_get_pairs(mock_get_req, coinbase_loader):
    mock_get_req.return_value = sample_pairs_response
    pairs = coinbase_loader.get_pairs()
    assert len(pairs) == 2
    assert isinstance(pairs[0], Pair)
    assert pairs[0].id == "BTC-USD"
    assert pairs[0].base_currency == "BTC"
    assert pairs[0].quote_currency == "USD"

@patch.object(CoinbaseLoader, '_get_req')
def test_get_stats(mock_get_req, coinbase_loader):
    mock_get_req.return_value = sample_stats_response
    stats = coinbase_loader.get_stats("BTC-USD")
    assert isinstance(stats, Stat)
    assert stats.id == "BTC-USD"
    assert stats.base_currency == "BTC"
    assert stats.quote_currency == "USD"

@patch.object(CoinbaseLoader, '_get_req')
@pytest.mark.parametrize("granularity", [Granularity.ONE_DAY, Granularity.ONE_HOUR])
def test_get_historical_data(mock_get_req, coinbase_loader, granularity):
    mock_get_req.return_value = sample_historical_data_response
    historical_data = coinbase_loader.get_historical_data("BTC-USD", datetime(2021, 6, 30), datetime(2021, 7, 1), granularity)
    assert isinstance(historical_data, HistoricalData)
    assert len(historical_data.data) == 2
    assert historical_data.data[0].timestamp == 1625097600
    assert historical_data.data[0].low == 33513.57
    assert historical_data.data[0].high == 33687.53
    assert historical_data.data[0].open == 33600.00
    assert historical_data.data[0].close == 33653.99
    assert historical_data.data[0].volume == 28.36152462

if __name__ == "__main__":
    pytest.main()