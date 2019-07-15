import logging
from tshcal.common.file_utils import get_basename_noext

# create logger
module_logger = logging.getLogger('tshcal.%s' % get_basename_noext(__file__))


def set_tsh_state(args):
    """set tsh configuration via commanding"""
    module_logger.debug('Setting tsh state.')
    return 42


def get_tsh_state():
    """get tsh configuration via commanding"""
    module_logger.debug('Getting tsh state.')
    return 42


def fake_query_tsh_sample_rate(tsh_id):
    """probably gonna be part of more extensive get/fetch or class definition"""
    if tsh_id == 'tshes-44':
        return 250.0
    else:
        raise Exception('using fake query/get/fetch -- so only a fake, tshes-44, works')
