import argparse
import os
import json

from .job_history import HistoryRecord, JobHistory

SYNC_HISTORY_LOG_FILE_NAME = 'syncengine-history.log'


def main():
    parser = argparse.ArgumentParser(description='Analyze the QNAP HBS log')
    parser.add_argument('hbs_log', help='Path of HBS diagnosis report')
    parser.add_argument('--sync-history', action='store_true',
                        dest='sync_history', help='Analyze sync file action')
    args = parser.parse_args()

    hbs_log = args.hbs_log

    if args.sync_history:
        for root, dirs, files in os.walk(hbs_log):
            if not root.endswith('system'):
                continue
            for dir in dirs:
                job_path = os.path.join(root, dir)
                job_log_path = os.path.join(job_path, 'log')
                print(f'Job Name: {dir}')
                analyze_sync_history(job_log_path)


def analyze_sync_history(log_path):
    if not os.path.exists(log_path):
        print(f'{log_path} not exists')
        return

    history_paths = get_history_paths(log_path)
    if len(history_paths) == 0:
        print(f'{SYNC_HISTORY_LOG_FILE_NAME} not exist under {log_path}')
        return

    job_history = get_job_history(history_paths)
    print_sync_history_report(job_history)


def get_history_paths(log_path):
    return get_log_paths(log_path, SYNC_HISTORY_LOG_FILE_NAME)


def get_log_paths(log_path, log_name):
    paths = list()
    for f in os.listdir(log_path):
        if log_name in f:
            paths.append(os.path.join(log_path, f))
    return paths


def get_job_history(history_paths) -> JobHistory:
    job_history = JobHistory()
    for p in history_paths:
        with open(p, 'r') as fp:
            for line in fp:
                h = json.loads(line)
                history_record = HistoryRecord(name=h['name'],
                                               timestamp=h['timestamp'],
                                               action=h['action'],
                                               exception=h['exception'],
                                               is_dir=h['is_dir'])
                job_history.add_history(history_record)
    return job_history


def print_sync_history_report(job_history):
    print(f'Job History from {job_history.start_time()} to {job_history.end_time()}')
    print(f'Total files: {job_history.total_files()}')
    print(f'Total folders: {job_history.total_folders()}')
    print('Action summary:')
    for action in job_history.action_types():
        print(f'  {len(job_history.get_files_by_action(action))} try to {action}')
    print('Exception summary:')
    for exception in job_history.exception_types():
        print(f'  {exception}: {len(job_history.get_files_by_exception(exception))}')

if __name__ == '__main__':
    main()
