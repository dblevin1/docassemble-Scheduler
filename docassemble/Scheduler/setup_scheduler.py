# pre-load
import datetime
import traceback
import sys
import copy
import os
import logging
from docassemble.webapp.app_object import app
from docassemble.webapp.user_database import alchemy_url as custom_alchemy_url
from docassemble.webapp.database import alchemy_connection_string
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.util import datetime_to_utc_timestamp, utc_timestamp_to_datetime
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from docassemble.base.config import daconfig
from docassemble.base.config import load as load_daconfig
from .scheduler_logger import (
    log,
    docassemble_log,
    get_logger,
    set_schedule_logger,
    error_notification,
    USING_SCHEDULE_LOGGER,
)
from sqlalchemy.exc import ProgrammingError
from docassemble.base.config import in_celery, in_cron

# Do not import this file anywhere

__all__ = []
bg_scheduler = None


def my_listener(event):
    if event.exception:
        clean_trace = str(event.traceback).replace("\n", "")
        log(
            "scheduler: The job crashed:"
            + f"{type(event.exception)}:{event.exception} TRACEBACK:{ clean_trace}"
        )
        docassemble_log(
            "scheduler: The job crashed:"
            + f"{type(event.exception)}:{event.exception} TRACEBACK:{ clean_trace}"
        )
        # fulltrace = traceback.format_exc()
        msg_body = f"Scheduler Exception: {str(event.exception)}\n\n"
        # msg_trace = fulltrace + "\n\nScheduler Traceback:" + str(event.traceback)
        msg_trace = "\n\nScheduler Traceback:" + str(event.traceback)
        msg_trace = (
            msg_trace.replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
        )
        msg_body = (
            msg_body.replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
        )
        error_notification(event.exception, msg_body, trace=msg_trace)


def job_missed_listener(event):
    log(
        f"Missed job '{event.job_id}' execution event of '{ event.scheduled_run_time.strftime('%m/%d/%y %I:%M %p') }'"
    )


def do_scheduler_setup():
    global bg_scheduler
    from . import scheduler_tasks

    jobs = dict(daconfig).get("scheduler", {})
    using_sql_jobstore = False
    if "use docassemble database" in jobs:
        using_sql_jobstore = bool(jobs.pop("use docassemble database"))
    loglevel = "INFO"
    if "log level" in jobs:
        loglevel = str(jobs.pop("log level")).upper()

    if len(jobs) > 0:
        if loglevel:
            logger_object = get_logger()
            if loglevel in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
                loglevelName = logging.getLevelName(loglevel)
                logger_object.setLevel(loglevelName)
            else:
                docassemble_log("Invalid log level, defaulting to INFO")
                log("Invalid log level, defaulting to INFO")
                loglevelName = logging.getLevelName("INFO")
                logger_object.setLevel(loglevelName)
        docassemble_log("Scheduler is starting...")
        log("Scheduler is starting...", "debug")
        jobstore = None
        if using_sql_jobstore:
            log("Setting up Scheduler with SQLAlchemyJobStore", "debug")
            sqlurl = alchemy_connection_string()
            jobstore = SQLAlchemyJobStore(sqlurl)
            jobstores = {"default": jobstore}
            bg_scheduler = BackgroundScheduler(jobstores=jobstores)
        else:
            log("Setting up Scheduler with default JobStore", "debug")
            bg_scheduler = BackgroundScheduler()
        bg_scheduler.add_listener(my_listener, EVENT_JOB_ERROR)
        bg_scheduler.add_listener(job_missed_listener, EVENT_JOB_MISSED)
        if not daconfig:
            load_daconfig()

        if not using_sql_jobstore:
            bg_scheduler.remove_all_jobs()

        existing_jobs_dict = dict()
        if jobstore is not None:
            try:
                existing_jobs = jobstore.get_all_jobs()
            except ProgrammingError as my_ex:
                if "UndefinedTable" in str(my_ex):
                    # Table doesn't exist yet, means this is the first run using the database, so no existing jobs to check
                    existing_jobs = []
                else:
                    raise
            for job in existing_jobs:
                existing_jobs_dict[job.id] = job
        added_job_names = set()

        for job_name in jobs:
            if "." not in job_name:
                log(
                    f"'{job_name}' must be in the format '[FILE_NAME].[FUNCTION_NAME]', skipping..."
                )
                continue
            job_data = copy.copy(jobs[job_name])
            job_data = dict(job_data)
            job_type = job_data.pop("type")
            func_args = []
            func_kwargs = {}
            if "args" in job_data:
                func_args = job_data.pop("args")
                try:
                    func_args = list(func_args)
                except:
                    log(f"Failed to parse {job_name} args")
                    func_args = []
            if "kwargs" in job_data:
                func_kwargs = job_data.pop("kwargs")
                try:
                    func_kwargs = dict(func_kwargs)
                except:
                    log(f"Failed to parse {job_name} kwargs")
                    func_kwargs = {}
            if "contextmanager" in job_data:
                func_kwargs["contextmanager"] = job_data.pop("contextmanager")

            log(f"Adding job '{job_name}'", "debug")
            job = bg_scheduler.add_job(
                scheduler_tasks.call_func_with_context,
                id=job_name,
                trigger=job_type,
                args=[job_name, *func_args],
                kwargs=func_kwargs,
                replace_existing=True,
                **job_data,
            )
            added_job_names.add(job_name)

            if job_name in existing_jobs_dict.keys():
                # Determine if job was missed, if so reschedule next run
                existing_job = existing_jobs_dict[job_name]

                # If job data is the same
                # trigger is an object either CrontTigger of IntervalTrigger
                if (
                    str(job.trigger) == str(existing_job.trigger)
                    and job.args == existing_job.args
                    and job.kwargs == existing_job.kwargs
                ):
                    existing_tz = existing_job.next_run_time.tzinfo
                    if existing_job.next_run_time < datetime.datetime.now(existing_tz):
                        log(
                            f"Existing job missed its runtime, '{job_name}' was scheduled for {existing_job.next_run_time.strftime('%m/%d/%y %I:%M %p')} rescheduling for right now",
                            "debug",
                        )
                        # offset run time because if runtime is in the past when .start() is called it will jump to the next runtime
                        nowish = datetime.datetime.now(existing_tz).replace(
                            microsecond=0
                        ) + datetime.timedelta(seconds=5)
                        job.modify(next_run_time=nowish)

        for existing_job_name in existing_jobs_dict.keys():
            if existing_job_name not in added_job_names and jobstore is not None:
                log(f"Deleting job from jobstore '{existing_job_name}'", "debug")
                jobstore.remove_job(existing_job_name)

        bg_scheduler.start()
        log(f"Started scheduler with '{len(jobs)}' jobs", "debug")
        for idx, job in enumerate(bg_scheduler.get_jobs()):
            log(
                f"Job '{idx+1}' '{job.id}' next_run_time={job.next_run_time.strftime('%m/%d/%y %I:%M %p')}"
            )

    else:
        docassemble_log(f"Background scheduler no jobs started")


def file_imported_by_docassemble_server():
    fullname_files_in_stack = [
        f.filename for f in traceback.extract_stack() if ".py" in f.filename
    ]
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
        f"setup_scheduler must be imported by a docassemble server to work properly! Not setting up scheduler...",
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
                "scheduler: Setting up the scheduler Failed:"
                + f"{type(my_ex)}:{my_ex} { clean_trace}",
                "crtitical",
            )
            docassemble_log(
                "scheduler: Setting up the scheduler Failed:"
                + f"{type(my_ex)}:{my_ex} { clean_trace}"
            )
            error_notification(
                my_ex,
                "Setting up the scheduler Failed:" + str(my_ex),
                trace=traceback.format_exc(),
            )

elif __name__ == "__main__":
    from docassemble.base.util import zoneinfo
    import sys
    import time

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
        for idx, job in enumerate(bg_scheduler.get_jobs()):
            print(
                f"Job '{idx+1}' '{job.id}' next_run_time={job.next_run_time.strftime('%m/%d/%y %I:%M %p')}"
            )
            print("---")
    exit()

    from docassemble.webapp.server import (
        db,
        app,
        set_request_active,
        login_user,
        UserModel,
        create_new_interview,
        random_string,
    )
    from docassemble.base.logger import set_logmessage, default_logmessage
    from docassemble.webapp.daredis import r

    set_logmessage(default_logmessage)
    set_request_active(False)

    with app.app_context():
        my_user = None
        for user in UserModel.query.options(db.joinedload(UserModel.roles)).all():
            if user.nickname == "admin":
                my_user = user
                break

        with app.test_request_context(base_url="http://localhost/", path="interview"):
            login_user(my_user, remember=False)
            # Start a fake session so any created files are destroyed automatically
            try:
                ex = Exception("Testing my_error_notification")
                got = my_error_notification(ex, str(ex))
                ex = Exception("Testing da_error_notification")
                got = error_notification(ex, str(ex))
                print(got)
            except Exception as my_ex:
                print(f"{type(my_ex)}:{my_ex}")
    print()

    # funcs = [func for func in dir(MyBackgroundJobs) if callable(
    #    getattr(MyBackgroundJobs, func)) and not func.startswith("__")]

    # b = MyBackgroundJobs()
    # b.update_drive_read_location()
    # print()
