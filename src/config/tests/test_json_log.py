import json
import logging

from config.json_log import JSONFormatter


def _record(**kw):
    defaults = dict(
        name="regwatch", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello %s", args=("world",), exc_info=None,
    )
    defaults.update(kw)
    return logging.LogRecord(**defaults)


def test_format_emits_json_with_expected_keys():
    out = JSONFormatter().format(_record())
    data = json.loads(out)
    assert data["severity"] == "INFO"
    assert data["message"] == "hello world"   # args interpolated
    assert data["logger"] == "regwatch"
    assert "time" in data and data["time"]


def test_format_includes_exc_info_when_present():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        rec = _record(level=logging.ERROR, msg="failed", args=(), exc_info=sys.exc_info())
    data = json.loads(JSONFormatter().format(rec))
    assert data["severity"] == "ERROR"
    assert "boom" in data["exc_info"]
