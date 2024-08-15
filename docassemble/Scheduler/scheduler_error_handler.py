# do not pre-load
import datetime
import json
import sys
import tempfile
import traceback
from types import TracebackType
from typing import Any

from flask import request
from flask_login import current_user

from docassemble.base.config import daconfig
from docassemble.base.functions import log, server
from docassemble.base.generate_key import random_alphanumeric
from docassemble.webapp.app_object import app
from docassemble.webapp.da_flask_mail import Message

from .job_data import SchedulerJobConfig, get_callable, get_cur_job

__all__ = []


def handle_error(ex, job=None):
    if not isinstance(job, SchedulerJobConfig):
        job = get_cur_job()
    job_name = getattr(job, "name", None)
    job_error_handler = getattr(job, "error_handler", None)
    log(f"Error with job '{job_name}': {ex.__class__.__name__}:{ex}", "error")
    try:
        if job_error_handler:
            error_handler = get_callable(job_error_handler)
            error_handler(ex, job)
        else:
            error_notification(ex)
    except Exception as ex2:
        log(f"Error handling exception with job '{job_name}': {ex.__class__.__name__}:{ex}", "error")
        error_notification(ex2, "Error in custom error handler")


def get_stack_vars(err):
    """
    Powerful function to get all variables from the stack of an exception and all exception causes.
    Automatically filters out all variables starting with '__' and 'user_dict' and 'pre_user_dict'.
    Also filters out all variables from the docassemble.base and docassemble.webapp modules.

    Could be a security risk if used inappropriately.
    """
    from docassemble.base.functions import safe_json

    if isinstance(err, str):
        err = get_or_create_exception(err)
    try:
        ex_vars = {}
        while err is not None:
            err_str = f"{err.__class__.__name__}: {err}"
            ex_vars[err_str] = {}
            tb = err.__traceback__
            while tb is not None:
                try:
                    filename = tb.tb_frame.f_code.co_filename
                    if "docassemble/base/" in filename or "docassemble/webapp/" in filename or __file__ in filename:
                        ex_vars[err_str][str(tb.tb_frame)] = {}
                    else:
                        ex_vars[err_str][str(tb.tb_frame)] = {
                            k: v
                            for k, v in tb.tb_frame.f_locals.items()
                            if not (k.startswith("__") or "user_dict" == k or "pre_user_dict" == k)
                        }
                except Exception as exc1:
                    ex_vars[err_str][str(getattr(tb, "tb_frame", random_alphanumeric(10)))] = (
                        f"Error getting vars: {exc1.__class__.__name__}:{exc1}"
                    )
                tb = tb.tb_next
            err = err.__context__
        return safe_json(ex_vars)
    except Exception as exc:
        return {"error": f"Error getting vars: {exc.__class__.__name__}:{exc}\n"}


def get_or_create_exception(err=None):
    """
    Makes sure 'err' is an exception with a traceback.
    * if err is a string, it will try to find the original exception in the stack
    * if err is an exception without a traceback it will use the given exception and add a traceback
      * this happens if an exception is created but not raised
    * if err is None and no exception is currently raised, one will be created with the current stack
    """
    if isinstance(err, str):
        # Find original Exception in stack from string
        err_str = err.strip().split("\n")[0]
        ex = sys.exc_info()[1]
        possible_ex_str = []
        while ex and getattr(ex, "__context__", None):
            if ex and err_str in f"{ex.__class__.__name__}: {ex}":
                return ex
            possible_ex_str.append(f"{ex.__class__.__name__}: {ex}")
            ex = ex.__context__
        else:
            log(f"Exception not found in stack for {err_str=} {possible_ex_str=}")
    if isinstance(err, BaseException):
        if not getattr(err, "__traceback__", None):
            return _create_ex_with_traceback(type(err), str(err))
        return err
    _, ex, tb = sys.exc_info()
    if tb is None or ex is None:
        ex_type = type(ex) if ex is not None else Exception
        ex_str = str(ex) if ex is not None else str(err)
        return _create_ex_with_traceback(ex_type, ex_str)
    return ex


def _create_ex_with_traceback(ex_type, ex_msg) -> Exception:
    tb = None
    depth = 0
    while True:
        try:
            frame = sys._getframe(depth)
            depth += 1
        except ValueError:
            break
        tb = TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)
    return ex_type(ex_msg).with_traceback(tb)


def error_notification(
    err: BaseException | str | None, additional_message="", trace=None, the_vars: Any = None, app_str="Scheduler"
):
    """Send an email notification about an error.

    Args:
        err (BaseException | str | None): Will be converted to an exception with a traceback using 'get_or_create_exception'
        additional_message (str, optional): Any additional message to include. Defaults to "".
        trace (str, optional): trace to include in email, if not given one will be generated.
        the_vars (Any, optional): variables to include in email as a file, if not given it will try to get the variables from the stack. Will pass through docassemble.base.functions.safe_json before sending.
        app_str (str, optional): string to include in subject of the email. Defaults to "Scheduler".
    """
    err = get_or_create_exception(err)

    if the_vars is None or trace is None:
        tb = getattr(err, "__traceback__", None)
        if tb is None:
            # should never be none becaue of get_or_create_exception, but just in case
            err = _create_ex_with_traceback(type(err), str(err))
            tb = err.__traceback__
        if the_vars is None:
            the_vars = get_stack_vars(err)
        if tb is not None and trace is None:
            trace = "".join(traceback.format_exception(type(err), err, tb))
    if trace is None:
        trace = traceback.format_exc()
    import docassemble.webapp.server  # noqa: F401
    with app.app_context():
        _error_notification(err, additional_message, trace, the_vars, app_str)


def _error_notification(err, additional_message, trace, the_vars, app_str):
    from docassemble.base.functions import safe_json

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    recipient_email = daconfig.get("error notification email", None)
    if not recipient_email:
        return False
    if err.__class__.__name__ in ["CSRFError", "ClientDisconnected", "MethodNotAllowed"]:
        return
    email_recipients = []
    if isinstance(recipient_email, list):
        email_recipients.extend(recipient_email)
    else:
        email_recipients.append(recipient_email)
    errmess = str(err)[0:10000]  # set max size of error message
    additional_message_str = ""
    if additional_message:
        additional_message_str = f"<code>{additional_message}</code>".replace("\n", "<br>").replace(
            "  ", "&nbsp;&nbsp;"
        )

    try:
        referer = str(request.referrer)
    except Exception:
        referer = None
    try:
        url = str(request.url)
    except Exception:
        url = None
    try:
        email_address = current_user.email
    except Exception:
        email_address = None
    try:
        app_name = app.config["APP_NAME"]
    except Exception:
        app_name = daconfig.get("appname", "")

    try:
        the_key = "schedulererrornotification:" + str(err.__class__.__name__)
        existing = server.server_redis.get(the_key)
        existing = existing.decode("utf-8") if existing else 0  # type: ignore
        existing = int(existing) if str(existing).isdigit() else 0
        pipe = server.server_redis.pipeline()
        pipe.set(the_key, existing + 1)
        pipe.expire(the_key, 60)
        pipe.execute()
        if existing > 10:
            return
    except Exception as my_ex:
        additional_message_str += f"\nFailed to set redis key, {my_ex.__class__.__name__}:{my_ex}\n"
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
                fp.write(json.dumps(safe_json(the_vars), indent=2))
                json_filename = fp.name
        except Exception as my_ex:
            additional_message_str += f" Failed to load variables, {my_ex.__class__.__name__}:{my_ex}"
    msg = None
    if app_str:
        app_str = str(app_str) + " "
    try:
        try:
            html = (
                "<html>\n  <body>\n    <p>There was an error in the "
                + app_name
                + f" {app_str}application at {date_str}.</p>\n    <p>The error message was: {additional_message_str}</p>\n<pre>"
                + err.__class__.__name__
                + ": "
                + str(errmess)
                + "</pre>\n"
            )

            if trace:
                html += "<pre>" + str(trace) + "</pre>"
            if email_address:
                html += "<p>The user's email address was " + email_address + "</p>"
            if url and url != referer:
                html += "<p>The url was " + url + "</p>"
            if referer:
                html += "<p>The referrer was " + referer + "</p>"
            if "external hostname" in daconfig and daconfig["external hostname"] is not None:
                html += "<p>The external hostname was " + str(daconfig["external hostname"]) + "</p>"
            html += "\n  </body>\n</html>"
            msg = Message(
                app_name + f" {app_str}Error: " + err.__class__.__name__,
                recipients=email_recipients,
                html=html,
            )
            if json_filename:
                with open(json_filename, "r", encoding="utf-8") as fp:
                    msg.attach("variables.json", "application/json", fp.read())

            num_tries = 3
            for i in range(num_tries):
                try:
                    return server.send_mail(msg, config="default")  # type: ignore
                except Exception as zerr:
                    log(f"Failed to send email error notification try={i}:{err=} '{zerr=}'")
            return server.send_mail(msg, config="default")  # type: ignore
        except Exception as zerr:
            log(f"Failed to send email error notification:{err=} '{zerr=}' {traceback.format_exc()}")
            body = "There was an error in the " + app_name + f" {app_str}application\n.<p>Original Error:</p><pre>"
            try:
                body += err.__class__.__name__ + ": " + str(errmess)
            except Exception:
                body += "Err"
            body += "</pre>\nProcessing Error:"
            try:
                body += f"<pre>{zerr.__class__.__name__}:{str(zerr.__class__.__name__)}</pre>"
            except Exception:
                body += "<pre>Err</pre>"
            html = (
                "<html>\n  <body>\n    <p>There was an error in the "
                + app_name
                + f" {app_str}application.</p>\n  </body>\n</html>"
            )
            msg = Message(
                app_name + f" {app_str}Error: " + err.__class__.__name__,
                recipients=email_recipients,
                body=body,
                html=html,
            )
            if json_filename:
                with open(json_filename, "r", encoding="utf-8") as fp:
                    msg.attach("variables.json", "application/json", fp.read())
            log(f"Re-Trying to Send my_error_notification:{msg.subject=}:{msg.html=}")
            return server.send_mail(msg, config="default")  # type: ignore
    except Exception as my_ex:
        log(f"Failed to send email error notification:{err=} '{my_ex=}' {traceback.format_exc()}")
        pass
    return False
