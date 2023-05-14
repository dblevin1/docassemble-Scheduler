# do not pre-load
import importlib
import os
if __name__ == "__main__":
    import docassemble.base.config
    #docassemble.base.config.load(arguments=remaining_arguments, in_cron=True)
    docassemble.base.config.load()

from docassemble.webapp.worker_common import bg_context, worker_controller
try:
    from .scheduler_logger import log, docassemble_log, set_schedule_logger
except:
    from docassemble.Scheduler.scheduler_logger import log, docassemble_log, set_schedule_logger


__all__ = []
SCHEDULER_PACKAGE = "docassemble.Scheduler"
SCHEDULER_TASK_MODULES = {}


def _import_module_and_get_func(job_name):
    # First try to find package in current
    tasksdir = os.path.join(os.path.dirname(__file__), 'tasks')
    modulelist = job_name.split('.')
    filename = modulelist.pop(0)
    job_module = None
    if str(filename)+".py" in os.listdir(tasksdir):
        package_name = f"{SCHEDULER_PACKAGE}.tasks"
        module_name = f"{ package_name }.{ filename }"
        try:
            job_module = importlib.import_module(module_name)
            #to_call = module_name + "." + ".".join(modulelist)
            log(f"Successfully imported {module_name}", 'debug')
        except Exception as my_ex:
            log(f"Error importing '{module_name}' from scheduler tasks directory: Exception:{type(my_ex)}:{my_ex}", 'critical')
    else:
        modulelist = job_name.split('.')
        funcname = modulelist.pop(-1)
        modulename = ".".join(modulelist)
        try:
            job_module = importlib.import_module(modulename)
            log(f"Successfully imported {modulename}", 'debug')
            #to_call = job_name
        except Exception as my_ex:
            log(f"Error importing '{job_name}' from scheduler tasks directory: Exception:{type(my_ex)}:{my_ex}", 'critical')

    if job_module is not None:
        job_func = getattr(job_module, job_name.split('.')[-1])
        if callable(job_func):
            return job_func
        else:
            log(f"Error importing '{job_name}', got job is not callable {job_func=}", 'critical')


def _get_custom_context_cls(contextmanager):
    contextmanager = str(contextmanager)
    tasksdir = os.path.join(os.path.dirname(__file__), 'tasks')
    contextmanager_list = contextmanager.split('.')
    if contextmanager_list[0]+".py" in os.listdir(tasksdir):
        contextmanager_module = f"{ SCHEDULER_PACKAGE }.tasks.{ contextmanager_list[0] }"
        contextmanager_class = contextmanager_list[-1]
    else:
        contextmanager_class = contextmanager_list.pop(-1)
        contextmanager_module = ".".join(contextmanager_list)
    ctx_mod = importlib.import_module(contextmanager_module)
    ctx_cls = getattr(ctx_mod, contextmanager_class)
    return ctx_cls


def _call_func(job_name, *pargs, **kwargs):
    retVal = None
    func_name = str(job_name).split(' ')[0]
    job_func = _import_module_and_get_func(func_name)
    if job_func:
        retVal = job_func(*pargs, **kwargs)
    else:
        log("Could not get function from '{job_name}'", 'warning')
    if retVal:
        log(f"'{job_name}' returned '{retVal}'", 'info')


def call_func_with_context(job_name, *pargs, **kwargs):
    job_name = str(job_name)
    with bg_context():
        log(f"Calling task '{job_name}'")
        if 'contextmanager' in kwargs:
            contextmanager = str(kwargs.pop('contextmanager'))
            ctx_cls = _get_custom_context_cls(contextmanager)
            with ctx_cls():
                log(f"Successfully started context:'{contextmanager}'", 'debug')
                _call_func(job_name, *pargs, **kwargs)
        else:
            _call_func(job_name, *pargs, **kwargs)


if 'playground' not in __file__ and __name__ != '__main__':
    set_schedule_logger()
    # import_tasks()
elif __name__ == '__main__':
    from docassemble.base.logger import default_logmessage, set_logmessage
    log("Main code...")
    worker_controller.initialize()
    set_logmessage(default_logmessage)
    # import_tasks()
    # call_func_with_context('test.heartbeat')
    # call_func_with_context('med_test.get_meds')
    print()
    call_func_with_context('docassemble.HappyAcres.tasks.scheduler_tasks.check_db',
                           contextmanager='docassemble.HappyAcres.tasks.utils.SchedulerDatabaseContext')
    print()
