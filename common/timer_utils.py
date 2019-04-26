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


def print_bytes_counter(my_bc):
    print(my_bc)


class BytesCounter(object):

    def __init__(self):
        self.byte_count = 0
        self.start_time = datetime.datetime.now()

    def __str__(self):
        return 'sec = %f, count = %d bytes' % (self.total_seconds(), self.byte_count)

    def total_seconds(self):
        return (datetime.datetime.now() - self.start_time).total_seconds()

    def add(self, b):
        self.byte_count += b


if __name__ == '__main__':

    bc = BytesCounter()

    print("starting...")
    rt = RepeatedTimer(1, print_bytes_counter, bc)  # auto-starts, no need of rt.start()
    try:
        sleep(1)  # your long-running job goes here...

        bc.add(2)
        print(bc)

        sleep(1)

        bc.add(3)
        print(bc)

        sleep(1)

        bc.add(1)
        print(bc)

        sleep(2)
    finally:
        rt.stop()  # better in a try/finally block to make sure the program ends!
