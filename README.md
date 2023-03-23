# docassemble.Scheduler

This is a docassemble extension that uses [APScheduler](https://apscheduler.readthedocs.io/) to setup a scheduler

## Usage

Docassemble configuration example:

```
scheduler:
    test.heartbeat:
        type: interval
        minutes: 1
    test.heartbeat:
        type: cron
        day: 1
        hour: 0
        minute: 1
```

# Configuration

In the above example `test.heartbeat` refers to the function `heartbeat` in the file [test.py](https://github.com/dblevin1/docassemble-Scheduler/blob/eba18a912d2de72f2e748d82122b3504e661a2da/docassemble/Scheduler/tasks/test.py).
Note that any job files should be placed in the [tasks](https://github.com/dblevin1/docassemble-Scheduler/tree/master/docassemble/Scheduler/tasks) folder.

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


## Author

System Administrator, admin@admin.com

