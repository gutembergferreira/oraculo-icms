import logging
import os
from typing import Any

import structlog


class setup_logging:
    _configured = False

    @classmethod
    def configure(cls) -> None:
        if cls._configured:
            return

        timestamper = structlog.processors.TimeStamper(fmt="iso")

        shared_processors: list[Any] = [
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.dict_tracebacks,
        ]

        logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.EventRenamer("message"),
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
        )

        cls._configured = True
