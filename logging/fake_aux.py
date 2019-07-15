import logging

# create logger
module_logger = logging.getLogger('mane.aux')


class Auxiliary:
    def __init__(self):
        self.logger = logging.getLogger('mane.aux.Auxiliary')
        self.logger.info('creating an instance of Auxiliary')

    def do_something(self):
        self.logger.info('doing something')
        # actually do something here
        self.logger.info('done doing something')


def some_function():
    module_logger.info('received a call to "some_function"')
