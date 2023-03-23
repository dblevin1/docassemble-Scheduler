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

'''
def heartbeat():
    log = scheduler_logger.get_logger().info
    now_str = datetime.datetime.now().strftime("%m.%d.%Y %H.%M.%S")
    with open('/tmp/heartbeat_schedule.log', 'a+') as scd_log:
        scd_log.write(now_str + "\n")
    log("heartbeat=" + now_str)
    medications = db_orm_medication.Medications().get_all(include_inactive=False, raw=False)
    log(f"Got {len(medications)} medications")


def make_new_medications():
    from docassemble.base.functions import this_thread
    # TODO Fix this, throws threading error see admin email
    # get all active meds
    # change to this month
    log("LOCALS:" + str(locals()))
    log("GLOBALS:" + str(globals()))
    with app.app_context():
        medications = db_orm_medication.Medications().get_all(include_inactive=False, raw=False)
        medications = list(dict(medications).values())

        for med in medications:
            if med.log_month != datetime.datetime.now().month or med.log_year != datetime.datetime.now().year:
                org_med_obj = db_orm_medication.Medication('org_med_obj', id=med.id)
                org_med_obj.db_read()
                new_medication = org_med_obj.copy_deep('new_medication')
                org_med_obj.active = False
                org_med_obj.allow_db_write = True
                org_med_obj.db_save()
                org_med_obj.allow_db_write = False

                # Reset obj
                new_medication._nascent = True
                delattr(new_medication, 'id')

                new_medication.date_created = datetime.datetime.now()
                new_medication.log_month = datetime.datetime.now().month
                new_medication.log_year = datetime.datetime.now().year

                new_medication.allow_db_write = True
                new_medication.db_save()
                new_medication.allow_db_write = False

                orig_med_events = db_orm_med_administration.MedAdminEvent.get(org_med_obj.id)
                for orig_med_event in orig_med_events:
                    med_event_obj = db_orm_med_administration.MedAdminEvent('event')
                    #med_event_obj.id = orig_med_event['id']
                    med_event_obj.id = orig_med_event.id
                    med_event_obj.db_read()

                    # reset obj
                    med_event_obj._nascent = True
                    delattr(med_event_obj, 'id')

                    med_event_obj.medication_id = new_medication.id
                    repeat_start = as_datetime(med_event_obj.repeat_start)
                    med_event_obj.repeat_start = repeat_start.replace(
                        year=new_medication.log_year, month=new_medication.log_month)
                    med_event_obj.db_save()

                if not hasattr(new_medication, 'id'):
                    missing_list = []
                    for col_name in db_orm_medication.MedicationModel.__dict__.keys():
                        if col_name.startswith('_'):
                            continue
                        if not hasattr(new_medication, col_name):
                            missing_list.append(col_name)
                    raise TypeError(
                        f"Medication for this month not saved \nmissing={missing_list}\nobject={pprint.pformat(new_medication.__dict__)}")


def update_drive_read_location():
    from .location_handler import Locations
    from .cloud_files import Uploader

    read_path = Uploader.get_base_read_path()
    #write_path = Uploader.get_pathing_config().get('Write Only', '/mnt/wo/')

    locations = Locations()
    rclone_drive_names = set()
    for location in locations.elements:
        if hasattr(location, 'drive_name') and location.drive_name:
            rclone_drive_names.add(location.drive_name)
    log(f"Doing update for {rclone_drive_names=}")
    failure_msg = ""
    for configName in rclone_drive_names:
        read_dir = os.path.join(read_path, configName)
        if not os.path.exists(read_dir):
            os.makedirs(read_dir)

        args = f'"{configName}:/" "{read_dir}/" -v --config "/mnt/rclone.conf" --tpslimit 10 --ignore-checksum'
        #log(f"Faking run of 'rclone sync {args}'")
        proc = subprocess.run(f"rclone sync {args}", shell=True, capture_output=True)
        print(proc)
        if proc.returncode != 0:
            failure_msg += "FAILED SYNC " + configName
            log(f"Failed rclone sync {configName=} {proc=}")
    # if failure_msg:
    #    log(failure_msg)


def update_drive_write_location():
    from .location_handler import Locations
    from .cloud_files import Uploader

    #read_path = Uploader.get_pathing_config().get('Read Only', '/mnt/ro/')
    write_path = Uploader.get_pathing_config().get('Write Only', '/mnt/wo/')

    locations = Locations()
    rclone_drive_names = set()
    for location in locations.elements:
        if hasattr(location, 'drive_name') and location.drive_name:
            rclone_drive_names.add(location.drive_name)
    log(f"Doing update for {rclone_drive_names=}")
    failure_msg = ""
    for configName in rclone_drive_names:
        write_dir = os.path.join(write_path, configName)
        if not os.path.exists(write_dir):
            os.makedirs(write_dir)

        args = f'"{write_dir}" "{configName}:/" -v --config "/mnt/rclone.conf" --delete-empty-src-dirs --ignore-size --ignore-checksum'
        #log(f"Faking run of 'rclone move {args}'")
        proc = subprocess.run(f"rclone move {args}", shell=True, capture_output=True)
        print(proc)
        if proc.returncode != 0:
            failure_msg += "FAILED MOVE " + configName
            log(f"Failed rclone move {configName=} {proc=}")
    # if failure_msg:
    #    log(failure_msg)
'''


# Put functions above here ---

def call_func_with_context(job_name):
    global SCHEDULER_TASK_MODULES
    job_name = str(job_name)
    with bg_context():
        log(f"Calling task '{job_name}'")
        modulelist = job_name.split('.')
        filename = modulelist.pop(0)
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
            # globals()[job_name]()


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
    import_tasks()
elif __name__ == '__main__':
    from docassemble.base.logger import default_logmessage, set_logmessage
    log("Main code...")
    worker_controller.initialize()
    set_logmessage(default_logmessage)
    import_tasks()
    call_func_with_context('test.heartbeat')
    call_func_with_context('med_test.get_meds')
    print()
