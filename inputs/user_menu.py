#!/usr/bin/env python3

import logging

# create logger
module_logger = logging.getLogger('tshcal')


def menu(msg):
    msg += '\nEnter 1 to accept\n'
    msg += 'Enter 0 to exit\n'
    msg += '-> '
    choice = input(msg)
    return int(choice)


def prompt_user(prompt_str):
    while True:
        try:
            ans = menu(prompt_str)
            if ans == 1:
                resp = 'User pressed one to accept.'
                module_logger.debug(resp)
                print(resp)
                break
            elif ans == 0:
                resp = 'User pressed zero to exit.'
                module_logger.debug(resp)
                print(resp)
                break
            else:
                print('Invalid choice, try again.')
        except ValueError:
            err_msg = 'Invalid choice, try again.'
            module_logger.debug(err_msg)
            print(err_msg)


if __name__ == '__main__':
    prompt_user('My message here.')