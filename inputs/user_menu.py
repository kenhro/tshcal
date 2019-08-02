#!/usr/bin/env python3

import logging

# create logger
module_logger = logging.getLogger('tshcal')


def menu(msg):
    msg += '\nEnter 1 to accept/continue\n'
    msg += 'Enter 0 to exit\n'
    msg += '-> '
    module_logger.info('User being prompted as shown below:\n%s' % msg)
    choice = input(msg)
    module_logger.debug('User entered: %s' % choice)
    return int(choice)


def prompt_user(prompt_str):
    while True:
        try:
            ans = menu(prompt_str)
            if ans == 1:
                resp = 'User pressed one to accept.'
                module_logger.info(resp)
                print(resp)
                break
            elif ans == 0:
                resp = 'User pressed zero to exit.'
                module_logger.info(resp)
                print(resp)
                break
            else:
                print('Invalid choice, try again.')
        except ValueError:
            err_msg = 'Invalid choice, try again.'
            module_logger.info(err_msg)
            print(err_msg)
    return ans


if __name__ == '__main__':
    prompt_user('My message here.')