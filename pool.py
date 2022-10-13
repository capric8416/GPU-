# -*- coding: utf-8 -*-

from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import cpu_count
from threading import Event


class ThreadPool:
    def __init__(self, max_workers=None):
        self._executor = ThreadPoolExecutor(max_workers=max_workers or 2 * cpu_count() // 3)
        self._stopping = Event()
        self._stopped = Event()

    def submit(self, notify, task, *args, **kwargs):
        future = self._executor.submit(task, *args, **kwargs)
        if notify:
            future.add_done_callback(notify)
        return future

    def stopping(self, timeout=None):
        return self._stopping.wait(timeout=timeout)

    def stopped(self, timeout=None):
        return self._stopped.wait(timeout=timeout)

    def stop(self, wait=True):
        self._stopping.set()
        self._executor.shutdown(wait=wait)
        self._stopped.set()


class ProcessPool:
    def __init__(self, max_workers=None):
        self._executor = ProcessPoolExecutor(max_workers=max_workers or 2 * cpu_count() // 3)
        self._stopping = Event()
        self._stopped = Event()

    def submit(self, notify, task, *args, **kwargs):
        future = self._executor.submit(task, *args, **kwargs)
        if notify:
            future.add_done_callback(notify)
        return future

    def stopping(self, timeout=None):
        return self._stopping.wait(timeout=timeout)

    def stopped(self, timeout=None):
        return self._stopped.wait(timeout=timeout)

    def stop(self, wait=True):
        self._stopping.set()
        self._executor.shutdown(wait=wait)
        self._stopped.set()
