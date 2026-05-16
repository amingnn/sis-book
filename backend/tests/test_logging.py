import json
import logging

from app.logging import configure_logging, logger


def test_configure_logging_writes_structured_json(tmp_path):
    log_file = tmp_path / "logs" / "sis-book.log"

    configured_path = configure_logging(log_file, level="INFO", force=True)
    logger.info("结构化日志测试")
    logger.complete()

    assert configured_path == log_file
    assert log_file.exists()

    payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["record"]["message"] == "结构化日志测试"
    assert payload["record"]["level"]["name"] == "INFO"


def test_configure_logging_returns_active_path_when_already_configured(tmp_path):
    first_log_file = tmp_path / "first.log"
    second_log_file = tmp_path / "second.log"

    configured_path = configure_logging(first_log_file, force=True)
    reused_path = configure_logging(second_log_file)

    assert configured_path == first_log_file
    assert reused_path == first_log_file


def test_standard_logging_is_intercepted(tmp_path):
    log_file = tmp_path / "intercept.log"
    configure_logging(log_file, level="INFO", force=True)

    logging.getLogger("third_party").warning("标准库日志转接测试")
    logger.complete()

    payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["record"]["message"] == "标准库日志转接测试"
    assert payload["record"]["level"]["name"] == "WARNING"
