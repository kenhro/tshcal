import datetime
from time import sleep
from threading import Timer


class RepeatedTimer(object):

    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def hello(name):
    print("Hello %s!" % name)


def byte_counter(st, bc):
    dur = (datetime.datetime.now() - st).total_seconds()
    print(dur, bc.bytes)


class BytesCounter(object):

    def __init__(self, bytes):
        self.bytes = bytes
        self.start_time = datetime.datetime.now()

    def add(self, b):
        self.bytes += b


if __name__ == '__main__':

    bytes_count = BytesCounter(0)

    print("starting...")
    rt = RepeatedTimer(1, byte_counter, start_time, bytes_count)  # auto-starts, no need of rt.start()
    try:
        sleep(1)  # your long-running job goes here...
        bytes_count.add(2)
        sleep(1)
        bytes_count.add(3)
        sleep(1)
        bytes_count.add(1)
        sleep(2)
    finally:
        rt.stop()  # better in a try/finally block to make sure the program ends!
