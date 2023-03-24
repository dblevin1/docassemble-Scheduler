# docassemble.Scheduler

This is a docassemble extension that uses [APScheduler](https://apscheduler.readthedocs.io/) to setup a scheduler

## Usage

Docassemble configuration example:

```yml
scheduler:
    log level: debug
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
```

Write your own python functions by creating a file in the [tasks](https://github.com/dblevin1/docassemble-Scheduler/tree/master/docassemble/Scheduler/tasks) folder. See Below on how to configure it.

## Scheduler Logger

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

# Configuration

In the above example `test.heartbeat` refers to the function `heartbeat` in the file [test.py](https://github.com/dblevin1/docassemble-Scheduler/blob/eba18a912d2de72f2e748d82122b3504e661a2da/docassemble/Scheduler/tasks/test.py).
Note that any job files should be placed in the [tasks](https://github.com/dblevin1/docassemble-Scheduler/tree/master/docassemble/Scheduler/tasks) folder or should be configured to using the package and function name.

You can refer to functions using a package name and function name. For example if you have the demo package installed the configuration below will execute [get_time](https://github.com/jhpyle/docassemble/blob/master/docassemble_demo/docassemble/demo/gettime.py) every minute:
```yml
scheduler:
    docassemble.demo.gettime.get_time:
        type: interval
        minutes: 1
```

`log level` is optional and will default to INFO if not provided. The value is not case-sensitive. Available options are `debug`, `info`, `warning`, `error`, `critical`. 

## Types:

* `interval`: use when you want to run the job at fixed intervals of time
* `cron`: use when you want to run the job periodically at certain time(s) of day
* ~~`date`: use when you want to run the job just once at a certain point of time~~ **Not Supported**
  
## `Interval` Parameters

* `weeks` (int) - number of weeks to wait
* `days` (int) – number of days to wait
* `hours` (int) – number of hours to wait
* `minutes` (int) – number of minutes to wait
* `seconds` (int) – number of seconds to wait
  
See [APScheduler Triggers Interval](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html#module-apscheduler.triggers.interval) for more info

## `Cron` Parameters

* `year` (int|str) – 4-digit year
* `month` (int|str) – month (1-12)
* `day` (int|str) – day of month (1-31)
* `week` (int|str) – ISO week (1-53)
* `day_of_week` (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
* `hour` (int|str) – hour (0-23)
* `minute` (int|str) – minute (0-59)
* `second` (int|str) – second (0-59)

See [APScheduler Triggers Cron](https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html#module-apscheduler.triggers.cron) for more info

## Passing Arguments

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

## Author

System Administrator, admin@admin.com

