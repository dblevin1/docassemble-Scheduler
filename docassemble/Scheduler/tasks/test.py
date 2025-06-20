import time
import datetime
from docassemble.Scheduler.scheduler_logger import log


def test_long_running():
    log("Called test_long_running log", "info")
    time.sleep(10)
    log("Finished test_long_running log", "info")


def test_raise_exception():
    log("Called test_raise_exception log", "critical")
    raise Exception("Called test_raise_exception exc")


def heartbeat():
    now_str = datetime.datetime.now().strftime("%m.%d.%Y %H.%M.%S")
    with open("/tmp/heartbeat_schedule.log", "a+") as scd_log:
        scd_log.write(now_str + "\n")
    log("heartbeat=" + now_str)


def test_arbitrary_params(*pargs, **kwargs):
    log(f"{pargs=} {kwargs=}")
