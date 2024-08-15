# do not pre-load
from docassemble.webapp.worker_common import bg_context

from . import job_data
from .job_data import get_callable, SchedulerJobConfig
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
    job = job_data.registry[signum]
    job_data.current_job.signal_num = signum
    job_data.current_job.job_name = job.name
    job_data.current_job.job = job

    try:
        with bg_context():
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
