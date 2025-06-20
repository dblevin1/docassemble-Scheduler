# do not pre-load
from flask import has_request_context

from docassemble.base.config import daconfig

from . import job_data
from .job_data import SchedulerJobConfig, get_callable, is_running, set_is_running
from .scheduler_error_handler import handle_error
from .scheduler_logger import log

__all__ = []


def _call_job(job: SchedulerJobConfig):
    retVal = None

    func_name = str(job.name).split(" ")[0]
    job_func = get_callable(func_name)
    retVal = job_func(*job.pargs, **job.kwargs)
    if retVal:
        log(f"'{job.name}' returned '{retVal}'", "info")


def call_uwsgi_registered_task(signum):
    if is_running(signum):
        log(f"Signal {signum} is already running, skipping", "debug")
        return
    log(f"Starting signal {signum}", "debug")
    job = job_data.registry[signum]
    job_data.current_job.signal_num = signum
    job_data.current_job.job_name = job.name
    job_data.current_job.job = job

    app_ctx = None
    req_ctx = None
    try:
        set_is_running(signum, True)
        if not has_request_context():
            from docassemble.base.functions import reset_local_variables
            from docassemble.webapp.server import app

            url_root = daconfig.get("url root", "http://localhost") + daconfig.get("root", "/")
            url = url_root + "interview"
            app_ctx = app.app_context()
            app_ctx.push()
            req_ctx = app.test_request_context(base_url=url_root, path=url)
            req_ctx.push()
            reset_local_variables()
        log(f"Calling task '{job.name}'", "debug")
        if job.contextmanager:
            ctx_cls = get_callable(job.contextmanager)
            with ctx_cls():
                log(f"Successfully started context:'{job.contextmanager}'", "debug")
                _call_job(job)
        else:
            _call_job(job)
    except Exception as ex:
        handle_error(ex, job)
    finally:
        set_is_running(signum, False)
        if app_ctx:
            app_ctx.pop()
        if req_ctx:
            req_ctx.pop()
    log(f"Finished signal {signum}", "debug")
