import pytest
from app.middleware.sliding_window import SlidingWindowMiddleware


def test_below_limit_keeps_all():
    middleware = SlidingWindowMiddleware(max_messages=20)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
    processed = middleware._process_window(messages)
    assert len(processed) == 5
    assert not any(m.get("_summary") for m in processed)


def test_above_limit_splits_window():
    middleware = SlidingWindowMiddleware(max_messages=5)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
    processed = middleware._process_window(messages)
    window_only = [m for m in processed if m.get("_in_window")]
    summaries = [m for m in processed if m.get("_summary")]
    assert len(window_only) <= 5
    assert len(summaries) > 0


def test_summary_contains_message_preview():
    middleware = SlidingWindowMiddleware(max_messages=3)
    messages = [{"role": "user", "content": "hello world from user"}] * 5
    processed = middleware._process_window(messages)
    summary = next(m for m in processed if m.get("_summary"))
    assert "hello" in summary["content"]
