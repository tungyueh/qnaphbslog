from datetime import datetime
from operator import attrgetter


class SyncFileHistoryRecord:
    def __init__(self,
                 name,
                 timestamp,
                 action,
                 result,
                 exception,
                 is_dir,
                 ):
        self.name = name
        self.timestamp = timestamp
        self.action = action
        self.result = result
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

    def total_sync(self, action=None):
        if action is None:
            return len(self._history)

        count = 0
        for h in self._history:
            if h.action == action:
                count += 1
        return count

    def total_files(self):
        names = set()
        for h in self._history:
            if h.is_dir is False:
                names.add(h.name)
        return len(names)

    def total_folders(self):
        names = set()
        for h in self._history:
            if h.is_dir is True:
                names.add(h.name)
        return len(names)

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

    def get_files(self, *, action=None, result=None):
        files = set()
        for h in self._history:
            if action and action != h.action:
                continue
            if result and result != h.result:
                continue
            files.add(h.name)
        return files

    def get_sync(self, exception):
        synces = []
        for h in self._history:
            if h.exception == exception:
                synces.append(h)
        return synces

