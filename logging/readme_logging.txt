From https://stackoverflow.com/questions/15727420/using-python-logging-in-multiple-modules

Best practice is, in each module, to have a logger defined like this:

import logging
logger = logging.getLogger(__name__)
near the top of the module, and then in other code in the module do e.g.

logger.debug('My message with %s', 'variable data')
If you need to subdivide logging activity inside a module, use e.g.

loggerA = logging.getLogger(__name__ + '.A')
loggerB = logging.getLogger(__name__ + '.B')
and log to loggerA and loggerB as appropriate.

In your main program or programs, do e.g.:

def main():
    "your program code"

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('/path/to/logging.conf')
    main()
or

def main():
    import logging.config
    logging.config.fileConfig('/path/to/logging.conf')
    # your program code

if __name__ == '__main__':
    main()
