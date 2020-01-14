from typing import List

from .account import Account
from .job import Job

AccountList = List[Account]
JobList = List[Job]


class HybridBackupSync:
    def __init__(self,
                 hbs_version,
                 cc3_build_number,
                 accounts: AccountList,
                 jobs: JobList):
        self.hbs_version = hbs_version
        self.cc3_build_number = cc3_build_number
        self.accounts = accounts
        self.jobs = jobs

    def get_account(self, account_id):
        for account in self.accounts:
            if account.id == account_id:
                return account

    def job_types(self):
        job_types = list()
        for j in self.jobs:
            if j.job_type not in job_types:
                job_types.append(j.job_type)
        return job_types

    def get_job_by_type(self, job_type):
        jobs = list()
        for j in self.jobs:
            if j.job_type == job_type:
                jobs.append(j)
        return jobs
