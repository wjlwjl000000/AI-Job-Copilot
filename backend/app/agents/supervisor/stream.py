"""Shared queue for real-time chunk streaming from Synthesizer to SSE endpoint."""
import asyncio

_queues: dict[str, asyncio.Queue] = {}

def create(turn_id: str) -> asyncio.Queue:
    q = asyncio.Queue()
    _queues[turn_id] = q
    return q

def get(turn_id: str) -> asyncio.Queue | None:
    return _queues.get(turn_id)

def remove(turn_id: str):
    _queues.pop(turn_id, None)
