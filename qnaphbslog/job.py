from typing import Optional


class Job:
    def __init__(self, account_id, job_type, name):
        self.account_id = account_id
        self.job_type = job_type
        self.name = name

    def __str__(self):
        return f'Job(name: {self.name}, job_type: {self.job_type})'


class BackupJob(Job):
    def __init__(self, account_id, job_type, name, backup_type):
        super().__init__(account_id, job_type, name)
        self.backup_type = backup_type

    def __str__(self):
        return f'BackupJob(name: {self.name}, backup_type: {self.backup_type})'


class RestoreJob(Job):
    def __init__(self, account_id, job_type, name, restore_type):
        super().__init__(account_id, job_type, name)
        self.restore_type = restore_type

    def __str__(self):
        return f'RestoreJob(name: {self.name}, restore_type: {self.restore_type})'


class SyncJob(Job):
    def __init__(self, account_id, job_type, name, sync_direction, sync_operation):
        super().__init__(account_id, job_type, name)
        self.sync_direction = sync_direction
        self.sync_operation = sync_operation

    def __str__(self):
        return f'SyncJob(name: {self.name}, sync_direction: {self.sync_direction}, sync_operation: {self.sync_operation})'


def make_job(job_conf) -> Optional[Job]:
    if job_conf['_type'] != 'cloud':
        return None

    account_id = job_conf['account_id']
    name = job_conf['name']
    job_type = job_conf['job_type']
    if job_type == 'backup':
        return BackupJob(account_id, job_type, name, job_conf['backup.type'])
    elif job_type == 'restore':
        return RestoreJob(account_id, job_type, name, job_conf['restore.type'])
    else:
        return SyncJob(account_id, job_type, name, job_conf['sync.direction'], job_conf['sync.operation'])
