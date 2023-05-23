# do not pre-load
# You can import this module and check the below variable to see if the code is being executed by the Scheduler and using this context
IN_SCHEDULER_JOB = False

# Note it is safer to do imports inside the __enter__ and __exit__ functions


class SchedulerContext:
    def __enter__(self):
        global IN_SCHEDULER_JOB
        IN_SCHEDULER_JOB = True
        from ..scheduler_logger import log
        log("SchedulerContext Started!")

    def __exit__(self, exc_type, exc_value, exc_tb):
        from ..scheduler_logger import log
        log("SchedulerContext Ended!")
