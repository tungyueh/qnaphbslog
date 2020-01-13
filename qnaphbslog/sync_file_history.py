from datetime import datetime
from operator import attrgetter


class SyncFileHistoryRecord:
    def __init__(self,
                 name,
                 timestamp,
                 action,
                 exception,
                 is_dir,
                 ):
        self.name = name
        self.timestamp = timestamp
        self.action = action
        self.exception = exception
        self.is_dir = is_dir


class SyncFileHistory:
    def __init__(self):
        self._history = list()

    def add_history(self, history_record: SyncFileHistoryRecord):
        self._history.append(history_record)

    def start_time(self):
        self._history.sort(key=attrgetter('timestamp'))
        first_history = self._history[0]
        first_datetime = datetime.utcfromtimestamp(first_history.timestamp)
        return first_datetime

    def end_time(self):
        self._history.sort(key=attrgetter('timestamp'))
        last_history = self._history[-1]
        last_datetime = datetime.utcfromtimestamp(last_history.timestamp)
        return last_datetime

    def total_files(self):
        files_count = 0
        for h in self._history:
            if h.is_dir is False:
                files_count += 1
        return files_count

    def total_folders(self):
        folders_count = 0
        for h in self._history:
            if h.is_dir is True:
                folders_count += 1
        return folders_count

    def action_types(self):
        action_types = list()
        for h in self._history:
            if h.action not in action_types:
                action_types.append(h.action)
        return action_types

    def exception_types(self):
        exception_types = list()
        for h in self._history:
            if h.exception is None:
                continue
            if h.exception not in exception_types:
                exception_types.append(h.exception)
        return exception_types

    def get_files_by_action(self, action):
        files = list()
        for h in self._history:
            if h.action == action:
                files.append(h.name)
        return files

    def get_files_by_exception(self, exception):
        files = list()
        for h in self._history:
            if h.exception == exception:
                files.append(h.name)
        return files
