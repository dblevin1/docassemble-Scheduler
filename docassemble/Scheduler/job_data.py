import threading
from collections import namedtuple
from typing import Callable
import os
import importlib

SCHEDULER_PACKAGE = "docassemble.Scheduler"

SchedulerJobConfig = namedtuple(
    "SchedulerJobConfig", ["name", "type", "params", "pargs", "kwargs", "contextmanager", "error_handler"]
)
registry: dict[int, SchedulerJobConfig] = dict()
running = set()

current_job = threading.local()
current_job.job_name = None  # used by scheduler_logger
current_job.signal_num = None
current_job.job = None

def get_cur_job() -> SchedulerJobConfig | None:
    return getattr(current_job, "job", None)

def get_callable(name) -> Callable:
    name = str(name)
    if "." not in name:
        raise ValueError(f"'{name}' must be in the format '[FILE_NAME].[FUNCTION_NAME]'")
    tasksdir = os.path.join(os.path.dirname(__file__), "tasks")
    name_list = name.split(".")
    if name_list[0] + ".py" in os.listdir(tasksdir):
        name_module = f"{ SCHEDULER_PACKAGE }.tasks.{ name_list[0] }"
        name_class = name_list[-1]
    else:
        name_class = name_list.pop(-1)
        name_module = ".".join(name_list)
    mod = importlib.import_module(name_module)
    item = getattr(mod, name_class)
    if not callable(item):
        raise ValueError(f"'{name}' is not callable")
    return item