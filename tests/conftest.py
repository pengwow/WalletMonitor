import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

SAMPLE_API_POSITION = {
    "user": "0xe668c4300f51344d8e6cee6294cb9cd1fb5fb5ca",
    "symbol": "BTC",
    "positionSize": 51.37724,
    "entryPrice": 77472.5,
    "markPrice": None,
    "liqPrice": 74560.627,
    "leverage": 25,
    "marginBalance": 158852.26,
    "positionValueUsd": 3971306.52,
    "unrealizedPnL": -9016.94,
    "fundingFee": 0,
    "marginMode": "cross",
    "createTime": 1779692644333,
    "updateTime": 1779695280244,
    "labels": None,
}

SAMPLE_SHORT_POSITION = {
    "user": "0x2fca7140502e6e78bb0ef747354fb19774351cc4",
    "symbol": "BTC",
    "positionSize": -16.12885,
    "entryPrice": 77416.5,
    "liqPrice": 78271.635,
    "leverage": 40,
    "marginBalance": 31500.15,
    "positionValueUsd": 1246711.72,
    "unrealizedPnL": 1928.99,
    "fundingFee": 11.45,
    "marginMode": "isolated",
    "createTime": 1779692142612,
}

SAMPLE_LOW_LEVERAGE_POSITION = {
    "user": "0x5a7581618829f377a16be2338eabdd03fece0eaf",
    "symbol": "BTC",
    "positionSize": 17.96,
    "entryPrice": 77372.6,
    "liqPrice": 28468.909,
    "leverage": 5,
    "marginBalance": 277676.18,
    "positionValueUsd": 1388380.89,
    "unrealizedPnL": -1358.32,
    "fundingFee": -17.28,
    "marginMode": "cross",
    "createTime": 1779689326178,
}

SAMPLE_META_RESPONSE = {
    "universe": [
        {"szDecimals": 5, "name": "BTC", "maxLeverage": 40, "marginTableId": 56},
        {"szDecimals": 4, "name": "ETH", "maxLeverage": 25, "marginTableId": 55},
        {"szDecimals": 1, "name": "MATIC", "maxLeverage": 20, "marginTableId": 20, "isDelisted": True},
        {"szDecimals": 2, "name": "SOL", "maxLeverage": 20, "marginTableId": 54},
    ]
}

SAMPLE_LONG_SHORT_RESPONSE = {
    "code": 0,
    "msg": "success",
    "data": {"longCount": 156, "shortCount": 146},
}

SAMPLE_POSITIONS_RESPONSE = {
    "code": 0,
    "msg": "success",
    "data": [SAMPLE_API_POSITION, SAMPLE_SHORT_POSITION],
}


@pytest.fixture
def sample_api_position():
    return SAMPLE_API_POSITION.copy()


@pytest.fixture
def sample_short_position():
    return SAMPLE_SHORT_POSITION.copy()


@pytest.fixture
def sample_positions():
    return [SAMPLE_API_POSITION.copy(), SAMPLE_SHORT_POSITION.copy()]
