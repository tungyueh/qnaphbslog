def get_upload_bytes_per_second_key(job_type):
    if job_type == 'backup':
        return 'transfer_bytes_per_second'
    elif job_type == 'sync':
        return 'upload_bytes_per_second'
    return ''


def get_download_bytes_per_second_key(job_type):
    if job_type == 'restore':
        return 'transfer_bytes_per_second'
    elif job_type == 'sync':
        return 'download_bytes_per_second'
    return ''


class JobHistoryRecord:
    def __init__(self,
                 start_time,
                 elapse_time,
                 stop_time,
                 status,
                 upload_bytes_per_second=None,
                 download_bytes_per_second=None
                 ):
        self.start_time = start_time
        self.elapse_time = elapse_time
        self.stop_time = stop_time
        self.status = status
        self.upload_bytes_per_second = upload_bytes_per_second
        self.download_bytes_per_second = download_bytes_per_second