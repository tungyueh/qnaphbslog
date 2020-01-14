import argparse
import os
import json

from .hbs import HybridBackupSync, AccountList
from .account import Account
from .job import Job
from .sync_file_history import SyncFileHistoryRecord, SyncFileHistory

SYNC_HISTORY_LOG_FILE_NAME = 'syncengine-history.log'


def main():
    parser = argparse.ArgumentParser(description='Analyze the QNAP HBS log')
    parser.add_argument('hbs_log', help='Path of HBS diagnosis report')
    parser.add_argument('--hbs-summary', action='store_true',
                        dest='hbs_summary', help='Print HBS summary')
    parser.add_argument('--sync-history', action='store_true',
                        dest='sync_history', help='Analyze sync file action')
    args = parser.parse_args()

    hbs_log_path = args.hbs_log

    if not os.path.exists(hbs_log_path):
        print(f'{hbs_log_path} not exists')

    if args.hbs_summary:
        hbs_version = get_hbs_version(hbs_log_path)
        cc3_version = get_cc3_version(hbs_log_path)
        accounts = get_accounts(hbs_log_path)
        jobs = get_jobs(hbs_log_path)
        hbs = HybridBackupSync(hbs_version, cc3_version, accounts, jobs)
        print_hbs_summary(hbs)

    if args.sync_history:
        jobs = get_jobs(hbs_log_path)
        for job in jobs:
            if job.job_type != 'sync':
                continue
            job_log_path = get_job_log_path(hbs_log_path, job.name)
            print_sync_history(job.name, job_log_path)


def get_hbs_version(hbs_log_path):
    qpkg_conf_path = os.path.join(hbs_log_path, 'qpkg.conf')
    with open(qpkg_conf_path, 'r') as fp:
        hbs_section = False
        for line in fp:
            if 'HybridBackup' in line:
                hbs_section = True
            if hbs_section and 'Version' in line:
                hbs_version = line.split()[-1]
                return hbs_version


def get_cc3_version(hbs_log_path):
    cc3_build_number_path = os.path.join(hbs_log_path, 'cc3_build_number')
    with open(cc3_build_number_path, 'r') as fp:
        cc3_build_number = int(fp.read())
    return cc3_build_number


def get_accounts(hbs_log_path):
    config = get_config(hbs_log_path)
    accounts = list()
    for acc in config['accounts']:
        if acc['_type'] == 'cloud':
            account = Account(_id=acc['_id'],
                              provider_type=acc['remote.provider_type'],
                              name=acc['name'])
            accounts.append(account)
    return accounts


def get_jobs(hbs_log_path):
    config = get_config(hbs_log_path)
    jobs = list()
    for j in config['jobs']:
        if j['_type'] == 'cloud':
            job = Job(account_id=j['account_id'],
                      job_type=j['job_type'],
                      name=j['name'])
            jobs.append(job)
    return jobs


def get_config(hbs_log_path):
    config_path = os.path.join(hbs_log_path, 'config.json')
    with open(config_path, 'r') as fp:
        content = fp.read()
        config = json.loads(content)
    return config


def print_hbs_summary(hbs: HybridBackupSync):
    print('HybridBackupSync Summary')
    print(f'HBS version: {hbs.hbs_version}')
    print(f'CC3 version: {hbs.cc3_build_number}')
    print(f'Accounts total: {len(hbs.accounts)}')
    for account in hbs.accounts:
        print(f'  name: {account.name}, provider type: {account.provider_type}')
    print(f'Jobs total: {len(hbs.jobs)}')
    job_types = hbs.job_types()
    for job_type in job_types:
        print(f'{job_type} jobs total: {len(hbs.get_job_by_type(job_type))}')
        for job in hbs.get_job_by_type(job_type):
            account = hbs.get_account(job.account_id)
            print(f'  name: {job.name}, provider type: {account.provider_type}')


def get_job_log_path(hbs_log_path, job_name):
    for root, dirs, files in os.walk(hbs_log_path):
        if not root.endswith('system'):
            continue
        for dir in dirs:
            if dir == job_name:
                job_path = os.path.join(root, dir)
                job_log_path = os.path.join(job_path, 'log')
                return job_log_path


def print_sync_history(job_name, log_path):
    if not os.path.exists(log_path):
        print(f'{log_path} not exists')
        return

    history_paths = get_history_paths(log_path)
    if len(history_paths) == 0:
        print(f'{SYNC_HISTORY_LOG_FILE_NAME} not exist under {log_path}')
        return

    job_history = get_job_history(history_paths)
    print_sync_history_report(job_name, job_history)


def get_history_paths(log_path):
    return get_log_paths(log_path, SYNC_HISTORY_LOG_FILE_NAME)


def get_log_paths(log_path, log_name):
    paths = list()
    for f in os.listdir(log_path):
        if log_name in f:
            paths.append(os.path.join(log_path, f))
    return paths


def get_job_history(history_paths) -> SyncFileHistory:
    job_history = SyncFileHistory()
    for p in history_paths:
        with open(p, 'r') as fp:
            for line in fp:
                h = json.loads(line)
                history_record = SyncFileHistoryRecord(name=h['name'],
                                                       timestamp=h['timestamp'],
                                                       action=h['action'],
                                                       exception=h['exception'],
                                                       is_dir=h['is_dir'])
                job_history.add_history(history_record)
    return job_history


def print_sync_history_report(job_name, job_history):
    print(f'Job Name: {job_name}')
    if job_history.total_files() == 0:
        print('No Sync History')
        return
    print(f'Sync History from {job_history.start_time()} to {job_history.end_time()}')
    print(f'Total files: {job_history.total_files()}')
    print(f'Total folders: {job_history.total_folders()}')
    print('Action summary:')
    for action in job_history.action_types():
        print(f'  {len(job_history.get_files_by_action(action))} try to {action}')
    if len(job_history.exception_types()) == 0:
        print('No exception')
    else:
        print('Exception summary:')
        for exception in job_history.exception_types():
            print(f'  {exception}: {len(job_history.get_files_by_exception(exception))}')


if __name__ == '__main__':
    main()
