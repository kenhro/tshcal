import logging
from tshcal.logging import fake_aux


# create logger with 'mane'
logger = logging.getLogger('mane')
logger.setLevel(logging.DEBUG)

# create file handler which logs to DEBUG level
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # changed from ERROR to INFO

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s : %(lineno)d - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def run():
    logger.info('creating an instance of auxiliary_module.Auxiliary')
    a = fake_aux.Auxiliary()
    logger.info('created an instance of auxiliary_module.Auxiliary')
    logger.info('calling auxiliary_module.Auxiliary.do_something')
    a.do_something()
    logger.info('finished auxiliary_module.Auxiliary.do_something')
    logger.info('calling auxiliary_module.some_function()')
    fake_aux.some_function()
    logger.info('done with auxiliary_module.some_function()')


if __name__ == '__main__':
    run()
