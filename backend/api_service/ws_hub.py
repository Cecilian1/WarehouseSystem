"""Lightweight WebSocket broadcast hub.

Decouples write-path modules (alerts_engine, inventory_ops, ...) from the
`/ws/notify` connection handling in main.py: they just call `broadcast(...)`
without knowing about individual WebSocket connections.
"""

from __future__ import annotations

from typing import Any

from fastapi import WebSocket

_connections: set[WebSocket] = set()


def register(websocket: WebSocket) -> None:
    _connections.add(websocket)


def unregister(websocket: WebSocket) -> None:
    _connections.discard(websocket)


async def broadcast(message: dict[str, Any]) -> None:
    dead: list[WebSocket] = []
    for websocket in list(_connections):
        try:
            await websocket.send_json(message)
        except Exception:
            dead.append(websocket)
    for websocket in dead:
        _connections.discard(websocket)
