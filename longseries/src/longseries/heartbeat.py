from __future__ import annotations
from typing import Callable, TypeVar

import httpx

T = TypeVar("T")


class Heartbeat:
    def __init__(self, url: str, *, transport: httpx.BaseTransport | None = None):
        self.url = url
        self.transport = transport

    def success(self) -> None:
        raise NotImplementedError

    def fail(self) -> None:
        raise NotImplementedError


def run_with_heartbeat(fn: Callable[[], T], heartbeat: Heartbeat | None) -> T:
    raise NotImplementedError
