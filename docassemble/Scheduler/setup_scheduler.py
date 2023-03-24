# pre-load
import datetime
import traceback
import subprocess
import sys
import copy
import os
import logging
import requests
import json
import tempfile
import re
from bs4 import BeautifulSoup
# if __name__ == "__main__":
#    import docassemble.base.config
#    #docassemble.base.config.load(arguments=remaining_arguments, in_cron=True)
#    docassemble.base.config.load()
#from docassemble.webapp.server import error_notification as da_error_notification
#from docassemble.webapp.server import app
from docassemble.webapp.app_object import app
from docassemble.webapp.user_database import alchemy_url
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.util import datetime_to_utc_timestamp, utc_timestamp_to_datetime
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from docassemble.base.config import daconfig
from docassemble.base.config import load as load_daconfig
from docassemble.webapp.da_flask_mail import Message
import docassemble.base.functions
from .scheduler_logger import log, docassemble_log, get_logger, set_schedule_logger, error_notification
from docassemble.webapp.worker_common import workerapp, bg_context, worker_controller
#from .schedule_logger import set_schedule_logmessage
#from .schedule_logger import scheduler_the_logmessage as log

# Do not import this file anywhere

__all__ = []
bg_scheduler = None

'''
TODO: ----need to add tasks----
independent_crontab_tasks
sync groups to roles
syncFiles
rclone controller read
rclone controller write
db_backup
cp rclone.conf to /mnt
'''


def my_listener(event):
    if event.exception:
        clean_trace = str(event.traceback).replace('\n', '')
        log('scheduler: The job crashed:' + f"{type(event.exception)}:{event.exception} TRACEBACK:{ clean_trace}")
        docassemble_log('scheduler: The job crashed:' +
                        f"{type(event.exception)}:{event.exception} TRACEBACK:{ clean_trace}")
        #fulltrace = traceback.format_exc()
        msg_body = f"Scheduler Exception: {str(event.exception)}\n\n"
        #msg_trace = fulltrace + "\n\nScheduler Traceback:" + str(event.traceback)
        msg_trace = "\n\nScheduler Traceback:" + str(event.traceback)
        msg_trace = msg_trace.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;').replace('"', '&quot;')
        msg_body = msg_body.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;').replace('"', '&quot;')
        error_notification(event.exception, msg_body,
                           trace=msg_trace)


def call_task_func(job_func_name):
    log(f"Running '{job_func_name}'")
    import subprocess
    #from . import scheduler_tasks
    #from docassemble.webapp.app_object import app
    #import docassemble.base.functions
    func_name = re.sub(r'([^a-zA-Z])', '', job_func_name)
    python_path = sys.executable
    tasks_path = os.path.join(os.path.dirname(__file__), 'scheduler_tasks.py')

    args = [
        python_path,
        tasks_path,
        func_name
    ]
    proc = subprocess.run(args, capture_output=True)
    log(proc)
    if proc.returncode:
        procerr = proc.stderr.decode('utf-8')
        clean_trace = str(procerr).replace('\n', '')
        log('scheduler: The subprocess job crashed:' + f"{ clean_trace}")
        goterr = procerr.strip().split('\n')
        excname = goterr[-1]
        msg_body = excname + "\n\nSTDOUT:" + proc.stdout.decode('utf-8')
        error_notification(Exception(excname), msg_body,
                           trace=procerr, history='<p><b>Done.</b></p>')
    '''with app.app_context():
        #my_user = None
        # for user in UserModel.query.options(db.joinedload(UserModel.roles)).all():
        #    if user.nickname == 'admin':
        #        my_user = user
        #        break
        with app.test_request_context(base_url="http://localhost/", path="interview"):
            #login_user(my_user, remember=False)
            # globals()[job_name]()
            getattr(scheduler_tasks, job_func_name)()'''


def do_scheduler_setup():
    from . import scheduler_tasks
    #log("STACK:" + str(traceback.format_stack()))
    #sqlurl = alchemy_url('data db')
    #jobstore = SQLAlchemyJobStore(sqlurl)
    #jobstores = {'default': jobstore}
    #bg_scheduler = BackgroundScheduler(jobstores=jobstores)
    #executors = {'default': ProcessPoolExecutor(5)}
    #executors = executors
    bg_scheduler = BackgroundScheduler()
    bg_scheduler.add_listener(my_listener, EVENT_JOB_ERROR)
    if not daconfig:
        load_daconfig()

    jobs = dict(daconfig).get('scheduler', {})
    if jobs.get('log level', False):
        logger_object = get_logger()
        loglevel = str(jobs.pop('log level')).upper()
        if loglevel in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            loglevelName = logging.getLevelName(loglevel)
            logger_object.setLevel(loglevelName)
        else:
            log("Invalid log level, defaulting to INFO")

    if len(jobs) > 0:
        docassemble_log("Scheduler is starting...")
        log("Scheduler is starting...")

        bg_scheduler.remove_all_jobs()
        for job_name in jobs:
            if '.' not in job_name:
                log(f"'{job_name}' must be in the format '[FILE_NAME].[FUNCTION_NAME]', skipping...")
                continue
            job_data = copy.copy(jobs[job_name])
            job_data = dict(job_data)
            job_type = job_data.pop('type')
            auto_execute_late_job = False
            need_trigger_now = False
            if 'auto_execute_late_job' in job_data:
                auto_execute_late_job = job_data.pop('auto_execute_late_job')
            if 'execute_on_setup' in job_data:
                job_data.pop('execute_on_setup')
                need_trigger_now = True
            func_args = []
            func_kwargs = {}
            if 'args' in job_data:
                func_args = job_data.pop('args')
                try:
                    func_args = list(func_args)
                except:
                    log(f"Failed to parse {job_name} args")
                    func_args = []
            if 'kwargs' in job_data:
                func_kwargs = job_data.pop('kwargs')
                try:
                    func_kwargs = dict(func_kwargs)
                except:
                    log(f"Failed to parse {job_name} kwargs")
                    func_kwargs = {}

            '''existing_tz = None
            if auto_execute_late_job:
                try:
                    # lookup_job calls reconstitute_job which needs the function to exist
                    # May throw LookupError if it doesn't exist
                    existing_job = jobstore.lookup_job(job_name)
                except:
                    existing_job = None
                if existing_job is not None:
                    existing_tz = existing_job.next_run_time.tzinfo
                    if existing_job.next_run_time <= datetime.datetime.now(existing_tz):
                        # Need to execute stale job now
                        log(f"Executing stale job now: {job_name}")
                        need_trigger_now = True'''

            job = bg_scheduler.add_job(
                scheduler_tasks.call_func_with_context,
                id=job_name,
                trigger=job_type,
                args=[job_name, *func_args],
                kwargs=func_kwargs,
                replace_existing=True,
                **job_data
            )
            # if need_trigger_now:
            #    job.modify(next_run_time=datetime.datetime.now(existing_tz))
        bg_scheduler.start()
        log(f"Started scheduler with '{len(jobs)}' jobs", 'debug')
        for idx, job in enumerate(bg_scheduler.get_jobs()):
            log(f"Job '{idx+1}' '{job.id}' next_run_time={job.next_run_time.strftime('%m/%d/%y %I:%M %p')}", 'debug')

    else:
        docassemble_log(f"Background scheduler no jobs started")


if 'playground' not in __file__ and __name__ != '__main__':
    set_schedule_logger()
    with app.app_context():
        try:
            do_scheduler_setup()
        except Exception as my_ex:
            clean_trace = str(traceback.format_exc()).replace('\n', '')
            log('scheduler: Setting up the scheduler Failed:' + f"{type(my_ex)}:{my_ex} { clean_trace}")
            docassemble_log('scheduler: Setting up the scheduler Failed:' + f"{type(my_ex)}:{my_ex} { clean_trace}")
            error_notification(my_ex, "Setting up the scheduler Failed:" + str(my_ex),
                               trace=traceback.format_exc())

elif __name__ == '__main__':
    print(__name__)
    print(__file__)
    log("Main code...")
    with app.app_context():
        do_scheduler_setup()
    log("HERE")
    exit()

    from docassemble.webapp.server import db, app, set_request_active, login_user, UserModel, create_new_interview, random_string
    from docassemble.base.logger import set_logmessage, default_logmessage
    from docassemble.webapp.daredis import r
    set_logmessage(default_logmessage)
    set_request_active(False)

    with app.app_context():
        my_user = None
        for user in UserModel.query.options(db.joinedload(UserModel.roles)).all():
            if user.nickname == 'admin':
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

    #b = MyBackgroundJobs()
    # b.update_drive_read_location()
    # print()
