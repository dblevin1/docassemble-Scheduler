# do not pre-load
import importlib
import datetime
import logging
import os
import subprocess
import pprint
import json
import sys
if __name__ == "__main__":
    import docassemble.base.config
    #docassemble.base.config.load(arguments=remaining_arguments, in_cron=True)
    docassemble.base.config.load()
from docassemble.base.config import daconfig
from docassemble.base.util import as_datetime
from docassemble.HappyAcres import db_orm_med_administration
from docassemble.HappyAcres import db_orm_client
from docassemble.HappyAcres import db_orm_medication
from docassemble.HappyAcres import db_orm_audit
from docassemble.HappyAcres import db_orm_log
from docassemble.HappyAcres import db_orm_submission
from docassemble.HappyAcres.medication_checker import Medication_Checker
from docassemble.HappyAcres.location_handler import Locations
from docassemble.webapp.worker_common import workerapp, bg_context, worker_controller
try:
    from .scheduler_logger import log, docassemble_log, set_schedule_logger
except:
    from docassemble.Scheduler.scheduler_logger import log, docassemble_log, set_schedule_logger


__all__ = []
SCHEDULER_PACKAGE = "docassemble.Scheduler"
SCHEDULER_TASK_MODULES = {}


def call_func_with_context(job_name, *pargs, **kwargs):
    global SCHEDULER_TASK_MODULES
    job_name = str(job_name)
    to_call = ''
    job_module = None
    with bg_context():
        log(f"Calling task '{job_name}'")
        # First try to find package in current
        tasksdir = os.path.join(os.path.dirname(__file__), 'tasks')
        modulelist = job_name.split('.')
        filename = modulelist.pop(0)
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

        '''try:
            if to_call:
                to_call_list = to_call.split('.')
                to_call_first = to_call_list.pop(0)
                job_func = globals()[to_call_first]
                for module in to_call_list:
                    job_func = getattr(job_func, module)
        except Exception as my_ex:
            log(f"Error finding job function in globals {job_name=} {to_call=}:{type(my_ex)}:{my_ex}", 'critical')'''
        if job_module is not None:
            job_func = getattr(job_module, job_name.split('.')[-1])
            if callable(job_func):
                retVal = job_func(*pargs, **kwargs)
                if retVal:
                    log(f"'{job_name}' returned '{retVal}'", 'debug')
            else:
                log(f"Error importing '{job_name}', got job is not callable {job_func=}", 'critical')

        '''
        func_name_to_call = ".".join(modulelist)
        if filename not in SCHEDULER_TASK_MODULES:
            log(f"Error: File '{filename}' was not loaded correctly", 'critical')
            raise Exception(f"File '{filename}' was not loaded correctly")
        else:
            try:
                job_func = getattr(SCHEDULER_TASK_MODULES[filename], func_name_to_call)
            except:
                log(f"Error: Could not get function '{func_name_to_call}' from '{filename}'", 'critical')
                raise Exception(f"Could not get function '{func_name_to_call}' from '{filename}'")
            job_func()
            # globals()[job_name]()'''


def import_tasks():
    global SCHEDULER_TASK_MODULES
    SCHEDULER_TASK_MODULES = {}
    tasksdir = os.path.join(os.path.dirname(__file__), 'tasks')
    if not os.path.exists(tasksdir):
        log(f"Scheduler 'tasks' directory does not exist, not setting up any jobs:'{tasksdir}'")
    else:
        for pyfile in os.listdir(tasksdir):
            if '.py' not in pyfile:
                continue
            #module_name = f".tasks.{ os.path.splitext(pyfile)[0] }"
            # try:
            #    importlib.import_module(f".tasks.{ os.path.splitext(pyfile)[0] }", __file__)
            #    log(f"Imported task relative file: {module_name}")
            # except Exception as my_ex:
            #    log(
            #        f"Scheduler: Error importing relative {module_name} from scheduler tasks directory: Exception:{type(my_ex)}:{my_ex}")
            package_name = f"{SCHEDULER_PACKAGE}.tasks"
            pyfile = os.path.splitext(pyfile)[0]
            module_name = f"{ package_name }.{ pyfile }"
            try:
                loaded_module = importlib.import_module(module_name)
                #globals()['tasks'] = job_func
                SCHEDULER_TASK_MODULES[pyfile] = loaded_module
                log(f"Imported task file: '{module_name}'")
            except Exception as my_ex:
                log(f"Error importing '{module_name}' from scheduler tasks directory: Exception:{type(my_ex)}:{my_ex}")
    print()


if 'playground' not in __file__ and __name__ != '__main__':
    set_schedule_logger()
    # import_tasks()
elif __name__ == '__main__':
    from docassemble.base.logger import default_logmessage, set_logmessage
    log("Main code...")
    worker_controller.initialize()
    set_logmessage(default_logmessage)
    # import_tasks()
    call_func_with_context('test.heartbeat')
    call_func_with_context('med_test.get_meds')
    call_func_with_context('docassemble.HappyAcres.scheduler_tasks.make_new_medications')
    print()
