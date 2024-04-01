# do not pre-load
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import tempfile
import json
import sys
from bs4 import BeautifulSoup
import traceback
from docassemble.base.config import daconfig
from docassemble.base.config import load as load_daconfig
from docassemble.webapp.app_object import app
from docassemble.base.logger import logmessage as docassemble_log
from docassemble.webapp.worker_common import worker_controller
from docassemble.webapp.da_flask_mail import Message

if not daconfig:
    load_daconfig()

__all__ = []

SCHEDULE_LOGGER = None
USING_SCHEDULE_LOGGER = False


def get_logger():
    global SCHEDULE_LOGGER
    if SCHEDULE_LOGGER is None:
        SCHEDULE_LOGGER = logging.getLogger("scheduler")
        # if not scheduler_logger.hasHandlers():
        log_file = os.path.join("/usr/share/docassemble/log/", "scheduler.log")
        log_formatter = logging.Formatter(
            "scheduler: %(asctime)s %(levelname)s %(filename)s->%(funcName)s(%(lineno)d) %(message)s"
        )
        # rotating_file_handler = logging.handlers.RotatingFileHandler(
        rotating_file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            backupCount=7,
            encoding=None,
            delay=True,
        )
        rotating_file_handler.setFormatter(log_formatter)

        SCHEDULE_LOGGER.setLevel(logging.INFO)
        SCHEDULE_LOGGER.addHandler(rotating_file_handler)
        # log = scheduler_logger.info
    return SCHEDULE_LOGGER


def log(msg, lvl="info"):
    # lvl can be ('debug', 'info', 'warning', 'error', 'critical')
    global USING_SCHEDULE_LOGGER
    if not USING_SCHEDULE_LOGGER:
        if worker_controller.loaded:
            worker_controller.set_request_active(False)
        else:
            try:
                from docassemble.webapp.server import set_request_active

                set_request_active(False)
            except Exception as my_ex:
                print(f"{my_ex.__class__.__name__}:{my_ex}")
                pass
        config_log_lvl = dict(daconfig).get("scheduler", {}).get("log level")
        if not config_log_lvl:
            config_log_lvl = "info"
        config_log_lvl = str(config_log_lvl).upper()
        if not hasattr(logging, config_log_lvl):
            config_log_lvl = "DEBUG"
        if getattr(logging, config_log_lvl) < getattr(logging, str(lvl).upper()):
            return
        docassemble_log(f"Scheduler [{ str(lvl).upper() }]: { msg }")
    else:
        lvl = str(lvl).lower()
        if lvl in ("debug", "info", "warning", "error", "critical"):
            logger = get_logger()
            log_func = getattr(logger, lvl)
            log_func(str(msg), stacklevel=2)

    if str(lvl).lower() == "critical":
        try:
            # If we were already handling an exception include that
            etype, value, ex_tb = sys.exc_info()
            trace = ""
            if value is not None:
                trace = "Original Exception:\n"
                trace += traceback.format_exc() + "\n"
            trace += "Current Stack:\n" + "".join(traceback.format_stack())
            if value is not None:
                error_notification(
                    value, message=f"{value}\nMessage: {msg}\n", trace=trace
                )
            else:
                error_notification(Exception(msg), trace=trace)
        except Exception as my_ex:
            log(f"Failed to send email for a critical log entry:{type(my_ex)}:{my_ex}")
            try:
                error_notification(
                    Exception(msg),
                    message=f"{msg}\n\nFAILED TO SEND EMAIL for critical log entry:{type(my_ex)}:{my_ex}",
                )
            except:
                pass


def set_schedule_logger():
    global USING_SCHEDULE_LOGGER
    global log
    # log = get_logger().info
    USING_SCHEDULE_LOGGER = True


def error_notification(
    err, message=None, history=None, trace=None, referer=None, the_vars=None
):
    with app.app_context():
        my_error_notification(err, message, history, trace, referer, the_vars)


def my_error_notification(
    err, message=None, history=None, trace=None, referer=None, the_vars=None
):
    recipient_email = daconfig.get("error notification email", None)
    if not recipient_email:
        return False
    email_recipients = []
    if isinstance(recipient_email, list):
        email_recipients.extend(recipient_email)
    else:
        email_recipients.append(recipient_email)
    if message is None:
        errmess = str(err)
    else:
        errmess = (
            str(message)
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
        )
    try:
        if not worker_controller.loaded:
            worker_controller.initialize()
            worker_controller.set_request_active(False)
        the_key = "myerrornotification:" + str(err.__class__.__name__)
        existing = worker_controller.r.get(the_key)
        if existing == errmess:
            return
        # 300 sec = 5 minutes
        worker_controller.r.set(the_key, errmess, ex=300)
    except Exception as my_ex:
        log(f"Error setting 'myerrornotification' redis value:{type(my_ex)}:{my_ex}")
        raise
    json_filename = None
    if the_vars is not None and len(the_vars):
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                prefix="datemp",
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as fp:
                fp.write(json.dumps(the_vars, sort_keys=True, indent=2))
                json_filename = fp.name
        except:
            pass
    msg = None
    try:
        try:
            html = (
                "<html>\n  <body>\n    <p>There was an error in the "
                + app.config["APP_NAME"]
                + " application.</p>\n    <p>The error message was:</p>\n<pre>"
                + err.__class__.__name__
                + ": "
                + str(errmess)
                + "</pre>\n"
            )
            body = (
                "There was an error in the "
                + app.config["APP_NAME"]
                + " application.\n\nThe error message was:\n\n"
                + err.__class__.__name__
                + ": "
                + str(errmess)
            )
            # if trace is not None:
            #    body += "\n\n" + str(trace)
            #    html += "<pre>" + str(trace) + "</pre>"
            if history is not None:
                body += "\n\n" + BeautifulSoup(history, "html.parser").get_text("\n")
                html += history
            if trace is not None:
                body += "\n\n" + str(trace)
                html += "<pre>" + str(trace) + "</pre>"
            if (
                "external hostname" in daconfig
                and daconfig["external hostname"] is not None
            ):
                body += "\n\nThe external hostname was " + str(
                    daconfig["external hostname"]
                )
                html += (
                    "<p>The external hostname was "
                    + str(daconfig["external hostname"])
                    + "</p>"
                )
            html += "\n  </body>\n</html>"
            msg = Message(
                app.config["APP_NAME"] + " Scheduler error: " + err.__class__.__name__,
                recipients=email_recipients,
                body=body,
                html=html,
            )
            if json_filename:
                with open(json_filename, "r", encoding="utf-8") as fp:
                    msg.attach("variables.json", "application/json", fp.read())
            return my_send_email(msg)
        except Exception as zerr:
            log(str(zerr))
            body = (
                "There was an error in the " + app.config["APP_NAME"] + " application."
            )
            html = (
                "<html>\n  <body>\n    <p>There was an error in the "
                + app.config["APP_NAME"]
                + " application.</p>\n  </body>\n</html>"
            )
            msg = Message(
                app.config["APP_NAME"] + " Scheduler error: " + err.__class__.__name__,
                recipients=email_recipients,
                body=body,
                html=html,
            )
            if json_filename:
                with open(json_filename, "r", encoding="utf-8") as fp:
                    msg.attach("variables.json", "application/json", fp.read())
            return my_send_email(msg)
    except Exception as my_ex:
        log(f"Failed to send email for a critical log entry:{err=} '{my_ex}'")
        pass
    return False


def my_send_email(msg):
    mail_engine = app.extensions.get("mail")
    if not mail_engine:
        docassemble_log("mail_engine not setup")
        log("mail_engine not setup")
        return "mail_engine not setup"
    if not msg.sender:
        msg.sender = mail_engine.default_sender
    got = mail_engine.send(msg)
    return got
