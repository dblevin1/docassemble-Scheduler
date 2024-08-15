# pre-load
import copy
import os
import sys
import traceback

from docassemble.base.config import daconfig, in_celery, in_cron
from docassemble.base.config import load as load_daconfig
from docassemble.webapp.app_object import app

from . import job_data
from .scheduler_logger import (
    docassemble_log,
    error_notification,
    get_logger,
    log,
    set_schedule_logger,
)
from .job_data import SchedulerJobConfig

# Do not import this file anywhere

__all__ = []


def get_valid_scheduler_config():
    if not daconfig:
        load_daconfig()
    scheduler_config = dict(daconfig).get("scheduler", {})
    assert isinstance(scheduler_config, dict), "scheduler must be a dictionary"
    scheduler_config = copy.deepcopy(scheduler_config)
    loglevel = str(scheduler_config.pop("log level", "INFO")).upper()
    logger_object = get_logger()
    try:
        logger_object.setLevel(loglevel)
    except ValueError:
        log(f"Invalid log level '{loglevel}', defaulting to INFO", "warning")
        logger_object.setLevel("INFO")
    custom_error_handler = scheduler_config.pop("error handler", None)
    jobs: list[SchedulerJobConfig] = []
    for config_key, config_val in scheduler_config.items():
        if not isinstance(config_val, dict):
            log(f"Skipping invalid job config '{config_key}'", "warning")
            continue
        if config_val.get("type", None) not in ("cron", "interval"):
            log(f"Skipping invalid job type '{ config_val.get('type', None) }' for job '{config_key}'", "warning")
            continue
        job_type = config_val.pop("type", None)
        job_args = config_val.pop("args", [])
        job_kwargs = config_val.pop("kwargs", {})
        job_ctx = config_val.pop("contextmanager", None)
        job_error_handler = custom_error_handler or config_val.pop("error handler", None)
        job_params = {}
        if job_type == "cron":
            valid_params = ("minute", "hour", "day", "month", "weekday")
            for param in set(config_val.keys()).union(valid_params):
                if param not in valid_params:
                    log(f"Ignoring invalid parameter '{param}' for job '{config_key}'")
                    continue
                param_val = config_val.get(param, -1)
                if isinstance(param_val, str) and param_val.startswith("*/"):
                    param_val = int(param_val[2:]) * -1
                elif isinstance(param_val, str) and param_val == "*":
                    param_val = -1
                else:
                    try:
                        param_val = int(param_val)
                    except ValueError:
                        log(f"Invalid parameter value '{param_val}' for '{param}'")
                        break
                job_params[param] = param_val
            if set(job_params.keys()) != set(valid_params):
                log(f"Skipping job '{config_key}' with invalid parameters")
                continue
        elif job_type == "interval":
            valid_params = ("seconds", "minutes", "hours", "days")
            for param in set(config_val.keys()).union(valid_params):
                if param not in valid_params:
                    log(f"Ignoring invalid parameter '{param}' for job '{config_key}'")
                    continue
                param_val = config_val.get(param, 0)
                if not str(param_val).isdigit():
                    log(f"Invalid parameter value '{param_val}' for '{param}'")
                    break
                job_params[param] = int(param_val)
            if set(job_params.keys()) != set(valid_params):
                log(f"Skipping job '{config_key}' with invalid parameters")
                continue
            secs = int(job_params.get("seconds", 0))
            secs += int(config_val.get("minutes", 0)) * 60
            secs += int(config_val.get("hours", 0)) * 3600
            secs += int(config_val.get("days", 0)) * 86400
            job_params = {"seconds": secs}
        job_name = str(config_key)
        if "." not in job_name:
            log(f"'{job_name}' must be in the format '[FILE_NAME].[FUNCTION_NAME]', skipping...")
            continue
        jobs.append(
            SchedulerJobConfig(job_name, job_type, job_params, job_args, job_kwargs, job_ctx, job_error_handler)
        )
    return jobs


def do_scheduler_setup():
    from . import scheduler_tasks

    try:
        import uwsgi  # type: ignore
    except ImportError:
        log("do_scheduler_setup must be called within uwsgi, not setting up scheduler", "warning")
        return

    jobs = get_valid_scheduler_config()
    if len(jobs) == 0:
        log("No valid jobs found in config, not starting scheduler", "debug")
        return

    for idx, job in enumerate(jobs):
        # docassemble doesn't start spool or mules, so we'll use the regular workers
        uwsgi_worker = ""  # Ref: https://uwsgi-docs.readthedocs.io/en/latest/PythonModule.html#uwsgi.register_signal

        job_data.registry[idx] = job
        uwsgi.register_signal(idx, uwsgi_worker, scheduler_tasks.call_uwsgi_registered_task)

        if job.type == "cron":
            uwsgi.add_cron(
                idx,
                job.params["minute"],
                job.params["hour"],
                job.params["day"],
                job.params["month"],
                job.params["weekday"],
            )
            log(f"Added uwsgi cron job, signal={idx} '{job.name}' with params {job.params}", "debug")
        elif job.type == "interval":
            uwsgi.add_timer(idx, job.params["seconds"])
            log(f"Added uwsgi interval job, signal={idx} '{job.name}' seconds={job.params['seconds']}", "debug")
        else:
            raise ValueError(f"uwsgi only supports cron and interval jobs, not '{job.type}'")

    log(f"Started scheduler with '{len(jobs)}' jobs", "debug")


def file_imported_by_docassemble_server():
    fullname_files_in_stack = [f.filename for f in traceback.extract_stack() if ".py" in f.filename]
    package_files_in_stack = [
        os.path.sep.join(f.split(os.path.sep)[-3:])
        for f in fullname_files_in_stack
        if f"{os.path.sep}docassemble{os.path.sep}" in f
    ]
    if len(package_files_in_stack) >= 2:
        if (
            package_files_in_stack[0] == "docassemble/webapp/run.py"
            and package_files_in_stack[1] == "docassemble/webapp/server.py"
        ):
            return True
    log(f"File Stack:{package_files_in_stack}", "debug")
    return False


if in_celery or in_cron:
    log(f"{in_celery=} {in_cron=}, Not setting up Scheduler...", "debug")
elif not file_imported_by_docassemble_server():
    log(
        "setup_scheduler must be imported by a docassemble server to work properly! Not setting up scheduler...",
        "debug",
    )
elif "playground" not in __file__ and __name__ != "__main__":
    set_schedule_logger()
    with app.app_context():
        try:
            do_scheduler_setup()
        except Exception as my_ex:
            clean_trace = str(traceback.format_exc()).replace("\n", "")
            log(
                "scheduler: Setting up the scheduler Failed:" + f"{type(my_ex)}:{my_ex} { clean_trace}",
                "crtitical",
            )
            docassemble_log("scheduler: Setting up the scheduler Failed:" + f"{type(my_ex)}:{my_ex} { clean_trace}")
            error_notification(
                my_ex,
                "Setting up the scheduler Failed:" + str(my_ex),
                trace=traceback.format_exc(),
            )

elif __name__ == "__main__":
    import sys
    import time

    from docassemble.base.util import zoneinfo

    # the below adds zoneinfo for pickle loading
    # Using the SQLAlchemyJobStore it pickles and unpickles the job
    # If a job was pickled in docassemble and needs to be unpickled here in main it needs zoneinfo
    if "zoneinfo" not in sys.modules:
        sys.modules["zoneinfo"] = zoneinfo
    log("Main code...")
    with app.app_context():
        do_scheduler_setup()
    log("HERE")
    while True:
        time.sleep(5)
    exit()
