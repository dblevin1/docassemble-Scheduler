# do not pre-load
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Any

from docassemble.base.config import daconfig
from docassemble.base.config import load as load_daconfig
from docassemble.base.logger import logmessage as docassemble_log
from docassemble.webapp.worker_common import worker_controller

if not daconfig:
    load_daconfig()

__all__ = []

SCHEDULE_LOGGER = None
USING_SCHEDULE_LOGGER = False


class ContextFilter(logging.Filter):
    def filter(self, record):
        from .job_data import current_job

        job_name = str(getattr(current_job, "job_name", ""))
        record.job_name = ".".join(job_name.split(".")[-2:])
        return True


def get_logger():
    global SCHEDULE_LOGGER
    if SCHEDULE_LOGGER is None:
        SCHEDULE_LOGGER = logging.getLogger("scheduler")
        # if not scheduler_logger.hasHandlers():
        log_file = os.path.join("/usr/share/docassemble/log/", "scheduler.log")
        log_formatter = logging.Formatter(
            "scheduler: %(asctime)s %(levelname)s %(job_name)s %(filename)s->%(funcName)s(%(lineno)d) %(message)s"
        )
        # rotating_file_handler = logging.handlers.RotatingFileHandler(
        rotating_file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            backupCount=7,
            encoding=None,
            delay=True,
        )
        rotating_file_handler.setFormatter(log_formatter)

        SCHEDULE_LOGGER.setLevel(logging.INFO)
        SCHEDULE_LOGGER.addHandler(rotating_file_handler)
        SCHEDULE_LOGGER.addFilter(ContextFilter())
        # log = scheduler_logger.info
    return SCHEDULE_LOGGER


def log(msg, lvl="info"):
    # lvl can be ('debug', 'info', 'warning', 'error', 'critical')
    global USING_SCHEDULE_LOGGER
    if not USING_SCHEDULE_LOGGER:
        # handle messages that are sent before the scheduler is setup
        if worker_controller.loaded:
            worker_controller.set_request_active(False)
        config_log_lvl = dict(daconfig).get("scheduler", {}).get("log level")
        if not config_log_lvl:
            config_log_lvl = "info"
        config_log_lvl = str(config_log_lvl).upper()
        if not hasattr(logging, config_log_lvl):
            config_log_lvl = "DEBUG"
        if getattr(logging, config_log_lvl) > getattr(logging, str(lvl).upper()):
            return
        docassemble_log(f"Scheduler [{ str(lvl).upper() }]: { msg }")
    else:
        lvl = str(lvl).lower()
        if lvl in ("debug", "info", "warning", "error", "critical"):
            logger = get_logger()
            log_func = getattr(logger, lvl)
            log_func(str(msg), stacklevel=2)

    if str(lvl).lower() == "critical":
        try:
            error_notification(None, msg)
        except Exception as my_ex:
            log(f"Failed to send email for a critical log entry:{type(my_ex)}:{my_ex}")


def set_schedule_logger():
    global USING_SCHEDULE_LOGGER
    USING_SCHEDULE_LOGGER = True


def error_notification(
    err: BaseException | str | None, additional_message="", trace=None, the_vars: Any = None, app_str="Scheduler"
):
    from .scheduler_error_handler import error_notification as error_notification_func

    return error_notification_func(err, additional_message, trace, the_vars, app_str)

if __name__ == "__main__":
    from docassemble.webapp.server import set_request_active
    from docassemble.base.logger import default_logmessage, set_logmessage
    
    set_logmessage(default_logmessage)
    set_request_active(False)
    log("Scheduler logger loaded", "debug")
    log("Test", "critical")
    log("Test2", "critical")
    _=0
