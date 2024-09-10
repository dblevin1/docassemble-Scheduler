# docassemble.Scheduler

This is a docassemble extension that uses [uWSGI cron system](https://uwsgi-docs.readthedocs.io/en/latest/Cron.html) to setup jobs that are interview independent.
The scheduling system built into docassemble needs an existing interview session with allow_cron=True to work and only has hourly granularity.
This package allows you to setup a scheduler with fine grain control of the execution params.
Some usecases might be, send a scheduled email report, newsletters, refreshing cached data.

Important notes about using this Scheduler:

* this package assumes you haven't changed the [uWSGI configuration](https://github.com/jhpyle/docassemble/blob/master/Docker/config/docassemble.ini.dist) 
* unchecked limit of **64 jobs**, this comes from [uWSGI Default Config](https://uwsgi-docs.readthedocs.io/en/latest/Cron.html#notes)
* a job will not wait for a previous job to complete
* a job will be run by the first available uWSGI **worker**, a [uWSGI mule](https://uwsgi-docs.readthedocs.io/en/latest/Mules.html) or [uWSGI spooler](https://uwsgi-docs.readthedocs.io/en/latest/Spooler.html) would be preferable but that would require editing the uWSGI config file and restarting uWSGI 
* your function must be defined in the global scope (no defining a function inside a function)
* the deault error handler will send an email to 'error notification email' with an attachment of all the variables in the current stack **(note depending on your use-case this may be a security/privacy issue)**

**Upgrading:** Versions 0.1.x use [APScheduler](https://apscheduler.readthedocs.io/) which had issues when accessing the database. Because each job executed in a new thread which was messing with the database engine connection. Using uWSGI means jobs are executed the same way a web request is handled (ie a forked process) and can use the existing database engine and session in docassemble.

# Usage

Docassemble configuration example:

```yml
scheduler:
  log level: debug
  # Example modules in the current package
  test.heartbeat:
    type: interval
    minutes: 1
  test.heartbeat:
    type: cron
    day: 1
    hour: 0
    minute: 1
  test.test_arbitrary_params:
    type: interval
    minutes: 1
    args:
        - positional_value_1
        - positional_value_2
    kwargs:
        optional_param: optional_value
  # Using the default admin playground
  docassemble.playground1.test_py_file.function_name:
    type: cron
    minute: "*/5"
```

### Install

 * In docassemble enter [https://github.com/dblevin1/docassemble-Scheduler](https://github.com/dblevin1/docassemble-Scheduler) for the GitHub URL on the Package Management page and click update.
 * Create your own python files with functions in a different package (or playground).
 * Add it to the docassemble configuration by referring to the package name, file name, and function name seperated by dots.


You may also fork this repo and write your own functions by creating a python file in the [tasks](https://github.com/dblevin1/docassemble-Scheduler/tree/master/docassemble/Scheduler/tasks) folder. Then uploading your fork to docassemble.


# Configuration
### This Package

In the above example `test.heartbeat` refers to the function `heartbeat` in the file [test.py](https://github.com/dblevin1/docassemble-Scheduler/blob/eba18a912d2de72f2e748d82122b3504e661a2da/docassemble/Scheduler/tasks/test.py). You can refer to jobs in this package by just using the filename and function name.

### Playground

You can setup a job to execute a playground module by using the following, replacing the items in brackets with your own values:

`docassemble.playground[USER_ID][PLAYGROUND_NAME].[FILE_NAME].[FUNCTION_NAME]`

* USER_ID = The id of the user who owns the playground
* PLAYGROUND_NAME = If using the base playgound leave blank
* FILE_NAME = The python file that exists in the 'Modules' section of the playground
* FUNCTION_NAME = Should be a function in the python file

### Custom Package

You can refer to a job using a package name, file name, and function name.

`[PACKAGE_NAME].[FILE_NAME].[FUNCTION_NAME]`

* PACKAGE_NAME = The full name of the package
* FILE_NAME = The python file that exists in the 'Modules' section of the playground
* FUNCTION_NAME = Should be a function in the python file

For example if you have the demo package installed the configuration below will execute [get_time](https://github.com/jhpyle/docassemble/blob/master/docassemble_demo/docassemble/demo/gettime.py) every minute:
```yml
scheduler:
    docassemble.demo.gettime.get_time:
        type: interval
        minutes: 1
```

## Types:

* `interval`: use when you want to run the job at fixed intervals of time
* `cron`: use when you want to run the job periodically at certain time(s) of day
  
## `Interval` Parameters

* `days` (int) – number of days to wait
* `hours` (int) – number of hours to wait
* `minutes` (int) – number of minutes to wait
* `seconds` (int) – number of seconds to wait

All values are converted to `seconds` and added together

## `Cron` Parameters

* `month` (int|str) – month (1-12)
* `day` (int|str) – day of month (1-31)
* `weekday` (int|str) – number of weekday (0-6)
* `hour` (int|str) – hour (0-23)
* `minute` (int|str) – minute (0-59)

Prefix any value with `*/` or `-` to run every *nth* value
* Example: `minute: "*/5"` means run **every 5 minutes** which is equivalent to `minute: -5`
* As opposed to `minute: 5` means **run when minute is 5**

Any value not given will be given a default value of `*` which is equivalent to `-1`
 
# Using the Scheduler Logger

The Scheduler Logger creates a new log file called `scheduler.log` which can be viewed from the web interface.
When writing your functions you may use the scheduler logger by using the below code. 
```python
# import the scheduler logger
from docassemble.Scheduler.scheduler_logger import log
# log usage: log(message, message_level='info')
# log a message, not specifing log_level deafults to 'info'
log("Hello World")
log("Hello World", 'debug')
log("Hello World", 'info')
log("Hello World", 'warning')
log("Hello World", 'error')
# logging a critical message automatically sends an email to the 'error notification email' docassemble configuration value
log("Hello World", 'critical')
```

`log level` is optional and will default to INFO if not provided. The value is not case-sensitive. Available options are `debug`, `info`, `warning`, `error`, `critical`. 

# Passing Arguments

To pass any arguments to a function use the configuration `args` and `kwargs`
```yml
scheduler:
  test.test_arbitrary_params:
    type: interval
    minutes: 1
    args:
      - positional_value_1
      - positional_value_2
    kwargs:
      optional_param: optional_value
```
The above configuration run `test_arbitrary_params` which will log any parameters passed to it. The above configuration will log: 
`pargs=('positional_value_1', 'positional_value_2') kwargs={'optional_param': 'optional_value'}`


# Calling the same Function

If you need to utilize the same function for different scheduled event just put a space and some characters at the end, ie:
```yml
scheduler:
  postgres_db_backup.run 1:
    type: cron
    hour: 4
    minute: 0
    args:
      - ['db', 'data db']
      - "/tmp/docassemble_db_backups/"
  postgres_db_backup.run 2:
    type: cron
    hour: 4
    minute: 30
    args:
      - ['db', 'data db']
      - "/tmp/docassemble_db_backups/"
```
These two task are the same but will be logged as `postgres_db_backup.run 1` and `postgres_db_backup.run 2`. Any characters after the space are ignored and only used to differentiate the tasks in the scheduling system.

# Custom Error Handler

You may setup a custom error handler using `error handler` per job or for all jobs (which overrides the per job configuration).
If your error handler raises an exception, or fails to be imported the default handler in scheduler_logger.my_error_notification will be used.

Your error handler function will be passed `exception` and the `job` data, Example error handler

```python
def error_handler(ex, job: job_data.SchedulerJobConfig):
  # job has these attributes:
  # "name", "type", "params", "pargs", "kwargs", "contextmanager", "error_handler"
  log(f"Scheduler Error with {job.name=}: {ex.__class__.__name__}:{ex}")
```

```yml
scheduler:
  error handler: some.error.handler
  test.heartbeat:
    type: interval
        error handler: some.error.handler
        minutes: 1
```

# Custom Context

Setting up a custom context is advanced but powerful, it allowes code to be executed before and after every job. The value for the tag `contextmanager` should be a module in the tasks directory like below, or it can be a full package name with the class such as `docassemble.Scheduler.tasks.test_context.SchedulerContext` this is equal to `test_context.SchedulerContext`. The class should implement `__enter__` and `__exit__`.
Example Config:

```yml
scheduler:
  test.heartbeat:
    type: interval
    contextmanager: test_context.SchedulerContext
    minutes: 1
```
It should be noted whether or not a custom context is supplied a context is already used which is provided by docassemble. It is the same context manager that is used for docassemble Celery tasks. See [the docassemble code here](https://github.com/jhpyle/docassemble/blob/2aa0178467e1902d2598d3066dfcca3308524da9/docassemble_webapp/docassemble/webapp/worker_common.py#L140)


