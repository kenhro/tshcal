import logging

# create logger
module_logger = logging.getLogger('main.tsh_commands')


def set_tsh_state(args):
    """set tsh configuration via commanding"""
    module_logger.info('set tsh state')
    return 42


def get_tsh_state():
    """get tsh configuration via commanding"""
    module_logger.info('get tsh state')
    return 42


def fake_query_tsh_sample_rate(tsh_id):
    """probably gonna be part of more extensive get/fetch or class definition"""
    if tsh_id == 'tshes-44':
        return 250.0
    else:
        raise Exception('using fake query/get/fetch -- so only a fake, tshes-44, works')
