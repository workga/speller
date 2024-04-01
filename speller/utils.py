from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class Timer:
    def __init__(self):
        self._start_dt = datetime.now()
        self._start_tm = time.monotonic()

    def time(self, message: str):
        logger.warn(
            '%s\tstart: %s\t finish: %s\tduration: %f',
            message, self._start_dt.strftime('%S.%f'), datetime.now().strftime('%S.%f'), time.monotonic() - self._start_tm
        )