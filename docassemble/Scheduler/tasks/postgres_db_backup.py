import subprocess
import os
import shutil
import tempfile
from datetime import datetime
from docassemble.Scheduler.scheduler_logger import log
from docassemble.base.config import daconfig, load as load_daconfig
if not daconfig:
    load_daconfig()


def run():
    backup_location = daconfig.get('custom db backup location')
    if not backup_location:
        log("Configuration 'custom db backup location' not found, not backing up anything", 'error')
        return
    databases_to_backup = daconfig.get('custom db backup')
    if not databases_to_backup:
        log("Configuration 'custom db backup' not found, not backing up anything", 'error')
        return
        
    log("Starting custom database backup")
    if isinstance(databases_to_backup, str):
        databases_to_backup = [databases_to_backup]
    databases_to_backup = list(databases_to_backup)

    for database_to_backup in databases_to_backup:
        database_config = daconfig.get(database_to_backup)
        if not database_config:
            log(f"Database '{database_to_backup}' not found in the configuration", 'error')
        backup_status = do_data_db_backup(database_config, backup_location)
        if not backup_status:
            log(f"Failed to backup database '{database_to_backup}', skipping", 'error')
    log("Finshed custom database backup")

def do_data_db_backup(database_config: dict, backup_location, use_tar=True):
    if not database_config:
        log("Error loading database config")
        return False
    db_user = database_config.get('user')
    db_pass = database_config.get('password')
    db_name = database_config.get('name')
    # hardcode localhost because we don't want to backup an offsite database
    db_host = 'localhost'
    if not db_user or not db_name or not db_pass:
        log("Error user, name, pass from config", 'error')
        return False

    backup_file = tempfile.NamedTemporaryFile()
    custom_env = os.environ.copy()
    custom_env['PGPASSWORD'] = db_pass
    try:
        log("Running pg_dump command...")
        pg_process = subprocess.run(f'pg_dump -F c --username="{db_user}" -h {db_host} "{db_name}" -f "{ backup_file.name }"', shell=True,
                                    stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE, env=custom_env)
    except:
        log("Caught Exception, Check logs", 'error')
        raise

    if pg_process.returncode != 0:
        log(f"pg_dump error:{pg_process.stdout}{pg_process.stderr}|{pg_process}", 'critical')
        return False
    
    if use_tar:
        tar_file = tempfile.NamedTemporaryFile(suffix='.tar.gz')
        tar_file_name = tar_file.name
        tar_file.close()
        tar_path = os.path.join(backup_location, f'{ datetime.now().strftime(f"%Y/%m/%d.%H.%M.%S_{db_name}") }.tar.gz')
        os.makedirs(os.path.dirname(tar_path), exist_ok=True)
        try:
            log("Tar sql file...")
            tar_process = subprocess.run(f'tar -czf "{tar_file_name}" "{backup_file.name}"', shell=True,
                                            stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE)
        except:
            log("Caught Exception, Check logs", 'error')
            raise

        if tar_process.returncode != 0:
            log(f"Tar error:{tar_process.stdout}{tar_process.stderr}", 'error')
            return False
        log("Moving tar file")
        shutil.move(tar_file_name, tar_path)
    else:
        zip_path = os.path.join(backup_location, f'{ datetime.now().strftime(f"%Y/%m/%d.%H.%M.%S_{db_name}") }.zip')
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        try:
            log("Zipping sql file...")
            zip_process = subprocess.run(f'zip -A -j "{zip_path}" "{backup_file.name}"', shell=True,
                                            stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE)
        except:
            log("Caught Exception, Check logs", 'error')
            raise

        if zip_process.returncode != 0:
            log(f"zip error:{zip_process.stdout}{zip_process.stderr}", 'error')
            return False

    backup_file.close()
    return True
    


if __name__ == '__main__':
    log("Main code...")
    run()
    print()