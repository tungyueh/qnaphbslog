import argparse
import os
import json
from collections import Counter

from .hbs import HybridBackupSync
from .account import Account
from .job import Job, make_job
from .job_history import JobHistory
from .job_history_record import (get_upload_bytes_per_second_key,
                                 get_download_bytes_per_second_key,
                                 JobHistoryRecord)
from .sync_file_history import SyncFileHistoryRecord, SyncFileHistory

SYNC_HISTORY_LOG_FILE_NAME = 'syncengine-history.log'


def main():
    parser = argparse.ArgumentParser(description='Analyze the QNAP HBS log')
    parser.add_argument('hbs_log', help='Path of HBS diagnosis report')
    parser.add_argument('--hbs-summary', action='store_true',
                        dest='hbs_summary', help='Print HBS summary')
    parser.add_argument('--job-history', action='store_true',
                        dest='job_history', help='Print Job History')
    parser.add_argument('--sync-history', action='store_true',
                        dest='sync_history', help='Analyze sync file action')
    parser.add_argument('--task', action='store_true',
                        dest='task', help='Analyze task')
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

    if args.job_history:
        jobs = get_jobs(hbs_log_path)
        for job in jobs:
            job_history_file = get_job_history_file(hbs_log_path, job.name)
            if job_history_file is None:
                continue
            with open(job_history_file, 'r') as fp:
                content = fp.read()

            job_history = JobHistory()
            upload_key = get_upload_bytes_per_second_key(job.job_type)
            download_key = get_download_bytes_per_second_key(job.job_type)
            for h in json.loads(content)['history']:
                record = JobHistoryRecord(start_time=h['start_time'],
                                          elapse_time=h.get('elapse_time'),
                                          stop_time=h['stop_time'],
                                          status=h['status'],
                                          upload_bytes_per_second=h.get(upload_key),
                                          download_bytes_per_second=h.get(download_key)
                                          )
                job_history.add(record)

            print_job_history(job.name, job_history)

    if args.sync_history:
        jobs = get_jobs(hbs_log_path)
        for job in jobs:
            if job.job_type != 'sync':
                continue
            job_log_path = get_job_log_path(hbs_log_path, job.name)
            print_sync_history(job.name, job_log_path)

    if args.task:
        jobs = get_jobs(hbs_log_path)
        for job in jobs:
            print_task(hbs_log_path, job)


def print_task(hbs_log_path, job):
    task_counter = count_task(hbs_log_path, job)
    total_tasks = 0
    for count in task_counter.values():
        total_tasks += count

    file_sizes = get_upload_file_size(hbs_log_path, job)
    mb = 1024*1024
    total_upload_files = 0
    num_file_size_smaller_than_5mb = 0
    num_file_size_5mb_to_100mb = 0
    num_file_size_100mb_to_1gb = 0
    num_file_size_larger_than_1gb = 0
    for size in file_sizes:
        total_upload_files += 1
        if size <= 5*mb:
            num_file_size_smaller_than_5mb += 1
        elif size <= 100*mb:
            num_file_size_5mb_to_100mb += 1
        elif size <= 1000*mb:
            num_file_size_100mb_to_1gb += 1
        else:
            num_file_size_larger_than_1gb += 1

    print(f'{job}\n'
          f'  Total submit {total_tasks} tasks\n'
          f'  Most common task: {task_counter.most_common(3)}\n'
          f'  Upload {total_upload_files} files\n'
          f'    ~5MB: {num_file_size_smaller_than_5mb}\n'
          f'    5MB~100MB: {num_file_size_5mb_to_100mb}\n'
          f'    100MB~1GB: {num_file_size_100mb_to_1gb}\n'
          f'    1GB~: {num_file_size_larger_than_1gb}'
          )


def count_task(hbs_log_path, job):
    task_counter = Counter()
    for file in list_job_log_file(hbs_log_path, job.name):
        with open(file, 'r') as fp:
            for line in fp:
                if 'task submitted:' not in line:
                    continue
                task_name = get_taks_name(line)
                task_counter.update({task_name: 1})
    return task_counter


def get_upload_file_size(hbs_log_path, job):
    file_sizes = list()
    for file in list_job_log_file(hbs_log_path, job.name):
        with open(file, 'r') as fp:
            for line in fp:
                if 'task submitted:' not in line:
                    continue
                task_name = get_taks_name(line)
                if task_name == 'UploadTask':
                    size = get_upload_size(line)
                    file_sizes.append(size)
    return file_sizes


def get_upload_size(line):
    size = int(line[line.find("'size': ") + len("'size': "):].split(',')[0])
    return size


def get_taks_name(line):
    start = line.find('task submitted: ') + len('task submitted: ')
    end = line.find('(')
    return line[start:end]


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
        job = make_job(j)
        if job:
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
            print(f'  {job} provider type: {account.provider_type}')


def get_job_history_file(hbs_log_path, job_name):
    for root, dirs, files in os.walk(hbs_log_path):
        if not root.endswith('system'):
            continue
        for dir in dirs:
            if dir == job_name:
                job_path = os.path.join(root, dir)
                job_history_path = os.path.join(job_path, 'job_history.json')
                return job_history_path


def print_job_history(job_name, job_history):
    print(f'Job Name: {job_name}, '
          f'total run {job_history.total_run_times()} times, '
          f'complete: {job_history.total_complete_times()}, '
          f'fail: {job_history.total_fail_times()}, '
          f'stopped: {job_history.total_stop_times()}')


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
                                                       result=h['result'],
                                                       exception=h['exception'],
                                                       is_dir=h['is_dir'])
                job_history.add_history(history_record)
    return job_history


def print_sync_history_report(job_name, job_history):
    jh = job_history
    print(f'Job Name: {job_name}')
    if jh.total_files() == 0:
        print('No Sync History')
        return
    print(f'Sync History from {jh.start_time()} to {jh.end_time()}')
    print(f'* Total sync: {jh.total_sync()}')
    print(f'* Total files: {jh.total_files()}')
    print(f'* Total folders: {jh.total_folders()}')
    print('\nAction summary:')
    for action in jh.action_types():
        sync_count =jh.total_sync(action=action)
        total_files = jh.get_files(action=action)
        success_files = jh.get_files(action=action, result='success')
        fail_files = jh.get_files(action=action, result='fail')

        print(f'* [{action.upper()}] try {sync_count} times, '
              f'total files: {len(total_files)}, '
              f'success: {len(success_files)}, '
              f'fail: {len(fail_files.difference(success_files))}')
    if len(jh.exception_types()) == 0:
        print('\nNo exception')
    else:
        print('\nException summary:')
        for exception in jh.exception_types():
            print(f'* {exception}: happens {len(jh.get_sync(exception=exception))} times')


def list_job_log_file(hbs_log_path, job_name):
    for root, dirs, files in os.walk(hbs_log_path):
        if not root.endswith(f'{job_name}/log'):
            continue
        for file in files:
            if 'engine.log' in file:
                yield os.path.join(root, file)


if __name__ == '__main__':
    main()
