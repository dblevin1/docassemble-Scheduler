
from docassemble.HappyAcres import db_orm_medication
import os
import datetime

from docassemble.Scheduler.scheduler_logger import log


def get_meds():
    medications = db_orm_medication.Medications().get_all(include_inactive=False, raw=False)
    log(f"Successfully Got {len(medications)} medications")
