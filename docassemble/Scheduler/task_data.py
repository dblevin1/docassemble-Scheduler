import threading

current_task_data = threading.local()
current_task_data.job_name = None
