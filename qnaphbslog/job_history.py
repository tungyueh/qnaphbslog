from typing import List

from qnaphbslog.job_history_record import JobHistoryRecord

JobHistoryList = List[JobHistoryRecord]


class JobHistory:
    def __init__(self):
        self._history: JobHistoryList = list()

    def add(self, history: JobHistoryRecord):
        self._history.append(history)

    def total_run_times(self):
        return len(self._history)

    def total_complete_times(self):
        count = 0
        for h in self._history:
            if h.status in ['Finished', 'Finished with warnings']:
                count += 1
        return count

    def total_fail_times(self):
        count = 0
        for h in self._history:
            if h.status == 'Failed':
                count += 1
        return count

    def total_stop_times(self):
        count = 0
        for h in self._history:
            if h.status == 'Stopped':
                count += 1
        return count

