from typing import Any

import pendulum
from dlt.sources.helpers.requests import Request, Response
from dlt.sources.helpers.rest_client.paginators import BasePaginator

from .utils import datetime_to_utc_ms


class WindowPaginator(BasePaginator):
    def __init__(self, window_size: pendulum.Duration):
        super().__init__()
        self._window_size = window_size
        self._window_start: pendulum.DateTime | None = None

    def init_request(self, request: Request) -> None:
        self._window_start = pendulum.from_timestamp(
            int(request.params["startTime"]) / 1000
        )
        self.update_request(request)

    def update_state(self, response: Response, data: Any | None = None) -> None:
        self._window_start += self._window_size
        self._has_next_page = self._window_start < pendulum.now("UTC")

    def update_request(self, request: Request) -> None:
        window_end = min(self._window_start + self._window_size, pendulum.now("UTC"))
        request.params.update(
            startTime=datetime_to_utc_ms(self._window_start),
            endTime=datetime_to_utc_ms(window_end),
        )
