import pendulum
import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

from .auth import BinanceAuth
from .paginator import WindowPaginator
from .utils import datetime_to_utc_ms


@dlt.source(name="binance")
def binance_source(
    symbols: list[str],
    api_key: str = dlt.secrets.value,
    private_key: str = dlt.secrets.value,
):
    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://api.binance.com",
            "auth": BinanceAuth(api_key, private_key),
        },
        "resource_defaults": {
            "primary_key": "id",
        },
        "resources": [
            {
                "name": "withdrawals",
                "endpoint": {
                    "path": "sapi/v1/capital/withdraw/history",
                    "params": {
                        "status": 6,
                        "startTime": "{incremental.start_value}",
                    },
                    "incremental": {
                        "cursor_path": "applyTime",
                        "initial_value": "2025-12-01 00:00:00",
                        "convert": lambda x: datetime_to_utc_ms(
                            pendulum.parse(x)
                        ),
                    },
                    "paginator": WindowPaginator(
                        window_size=pendulum.duration(months=1)
                    ),
                },
            },
            *[
                {
                    "name": f"trades_{symbol.lower()}",
                    "table_name": "trades",
                    "parallelized": True,
                    "endpoint": {
                        "path": "api/v3/myTrades",
                        "params": {
                            "symbol": symbol,
                            "fromId": "{incremental.start_value}",
                        },
                        "incremental": {
                            "cursor_path": "id",
                            "initial_value": 0,
                        },
                        "paginator": "single_page",
                    },
                }
                for symbol in symbols
            ],
        ],
    }

    yield from rest_api_resources(config)


def run_pipeline(symbols: list[str]) -> None:
    pipeline = dlt.pipeline(
        pipeline_name="binance_pipeline",
        destination="filesystem",
        dataset_name="binance",
    )

    pipeline.run(binance_source(symbols))
