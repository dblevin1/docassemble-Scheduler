import subprocess
import os
import shutil
import tempfile
from datetime import datetime
from docassemble.Scheduler.scheduler_logger import log
from docassemble.base.config import daconfig, load as load_daconfig
if not daconfig:
    load_daconfig()


def run(db_keys_to_backup, backup_location):
    log("Starting custom database backup")
    now = datetime.now() 
    if isinstance(db_keys_to_backup, str):
        db_keys_to_backup = [db_keys_to_backup]
    databases_to_backup = list(db_keys_to_backup)

    for database_to_backup in databases_to_backup:
        database_config = daconfig.get(database_to_backup)
        if not database_config:
            log(f"Database '{database_to_backup}' not found in the configuration", 'error')
        log(f"Backing up database '{database_to_backup}'")
        backup_status = do_data_db_backup(database_config)
        if backup_status:
            db_name = backup_status[0] 
            temp_dir = backup_status[1]
            tar_file(db_name, temp_dir.name, backup_location, now)
            temp_dir.cleanup()
        if not backup_status:
            log(f"Failed to backup database '{database_to_backup}', skipping", 'error')
    log("Finshed custom database backup")

def do_data_db_backup(database_config: dict):
    if not database_config:
        log("Error loading database config")
        return False
    db_user = database_config.get('user')
    db_pass = database_config.get('password')
    db_name = database_config.get('name')
    db_host = database_config.get("host")
    if not db_user or not db_name or not db_pass:
        log("Error user, name, pass from config", 'error')
        return False

    temp_dir = tempfile.TemporaryDirectory()
    sql_file = os.path.join(temp_dir.name, db_name)
    custom_env = os.environ.copy()
    custom_env['PGPASSWORD'] = db_pass
    try:
        log("Running pg_dump command...")
        pg_process = subprocess.run(f'pg_dump -F c --username="{db_user}" -h {db_host} "{db_name}" -f "{ sql_file }"', shell=True,
                                    stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE, env=custom_env)
        log(f"pg_dump output: stdout={pg_process.stdout}, stderr={pg_process.stderr}")
    except:
        log("Caught Exception, Check logs", 'error')
        raise

    if pg_process.returncode != 0:
        log(f"pg_dump error:{pg_process.stdout}{pg_process.stderr}|{pg_process}", 'critical')
        return False
    return (db_name, temp_dir)
    

def tar_file(db_name, temp_dir_name, backup_location, now=None):
    if not now:
        now = datetime.now()
    tar_file_name = str(db_name) + '.tar'
    try:
        log("Tar sql file...")
        args = f'tar -cf "{tar_file_name}" "{db_name}"'
        log(f"Running tar with args: {args}")
        tar_process = subprocess.run(args, shell=True,
                                        stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE,
                                        cwd=temp_dir_name)
        log(f"tar output: stdout={tar_process.stdout}, stderr={tar_process.stderr}")
    except:
        log("Caught Exception, Check logs", 'error')
        raise

    if tar_process.returncode != 0:
        log(f"Tar error:{tar_process.stdout}{tar_process.stderr}", 'error')
        return False
    log("Moving tar file")
    to_path = os.path.join(backup_location, now.strftime(f"%Y/%m/%d_%H.%M.%S_{db_name}.tar"))
    os.makedirs(os.path.dirname(to_path), exist_ok=True)
    shutil.move(os.path.join(temp_dir_name, tar_file_name), to_path)
    return True
    


if __name__ == '__main__':
    log("Main code...")
    run()
    print()