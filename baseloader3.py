import requests
import logging
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime
import json
import pytest
from pydantic import ValidationError

class BaseDataLoader:
    def __init__(self, endpoint=None, logger=None):
        self._base_url = endpoint
        if logger is None:
            logger = logging.getLogger('BASELDR')
        self._logger = logger
        self._logger.info("Створено екземпляр BaseDataLoader")

    def _get_req(self, resource, params=None):
        req_url = self._base_url + resource
        if params is not None:
            self._logger.debug(f"GET: url={req_url}, params={params}")
            response = requests.get(req_url, params=params)
        else:
            self._logger.debug(f"GET: url={req_url}")
            response = requests.get(req_url)
        self._logger.debug(f"RESPONSE: код={response.status_code}")
        if response.status_code != 200:
            msg = f"Не вдалося запросити дані з {req_url}, статус: {response.status_code}"
            if response.text:
                try:
                    json_response = response.json()
                    if 'message' in json_response:
                        msg += f", повідомлення: {json_response['message']}"
                except ValueError:
                    pass
            raise RuntimeError(msg)
        return response.json()  # повертаємо JSON



class Pair(BaseModel):
    id: str
    base: str
    quote: str

class GetPairsResponse(BaseModel):
    pairs: List[Pair]

class Stat(BaseModel):
    pair_id: str = Field(..., regex=r'^[A-Z]{3,5}[A-Z]{3,5}$', description="Pair ID in format BASEQUOTE, e.g., BTCUSD")
    volume: int = Field(..., ge=0, description="Trade volume must be a non-negative integer")
    price: float = Field(..., gt=0, description="Price must be a positive float")

    @validator('pair_id')
    def validate_pair_id(cls, value):
        if len(value) < 6 or len(value) > 10:
            raise ValueError('Pair ID length must be between 6 and 10 characters')
        return value

    @validator('price')
    def validate_price(cls, value):
        if value < 0.01:
            raise ValueError('Price must be at least 0.01')
        return value

class GetStatsResponse(BaseModel):
    stats: List[Stat]

class HistoricalDataEntry(BaseModel):
    timestamp: datetime
    pair_id: str
    price: float

class GetHistoricalDataResponse(BaseModel):
    historical_data: List[HistoricalDataEntry]

if __name__ == "__main__":
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelень)s - %(повідомлення)s')
    file_handler = logging.FileHandler('baseloader.log')
    file_handler.setFormatter(formatter)
    logger = logging.getLogger('BASELDR')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    loader = BaseDataLoader(endpoint='https://api.example.com', logger=logger)
    
    try:
        pairs_data = loader._get_req('/get_pairs')
        stats_data = loader._get_req('/get_stats')
        historical_data = loader._get_req('/get_historical_data')
    except RuntimeError as e:
        logger.error(e)
    
    
    try:
        pairs_response = GetPairsResponse(**pairs_data)
        stats_response = GetStatsResponse(**stats_data)
        historical_response = GetHistoricalDataResponse(**historical_data)
        
        print("Pairs Response:", pairs_response)
        print("Stats Response:", stats_response)
        print("Historical Data Response:", historical_response)
    except Exception as e:
        logger.error(f"Помилка при валідації даних: {e}")


valid_data = {
  "stats": [
    {"pair_id": "BTCUSD", "volume": 123456, "price": 40000.0},
    {"pair_id": "ETHUSD", "volume": 78910, "price": 2500.5}
  ]
}

invalid_data = {
  "stats": [
    {"pair_id": "BTC_USD", "volume": 123456, "price": 40000.0},  
    {"pair_id": "ETHUSD", "volume": -100, "price": 2500.5},  
    {"pair_id": "BTCUSD", "volume": 78910, "price": 0.005} 
  ]
}

def test_valid_stats():
    try:
        response = GetStatsResponse(**valid_data)
        assert len(response.stats) == 2
    except ValidationError as e:
        pytest.fail(f"Validation failed: {e}")

def test_invalid_stats():
    with pytest.raises(ValidationError):
        GetStatsResponse(**invalid_data)


if __name__ == "__main__":
    test_valid_stats()
    test_invalid_stats()
    print("Тести пройдено успішно")
