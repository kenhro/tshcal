import logging


def set_tsh(a):
    """set tsh configuration via commanding"""

    # start logging
    logger = logging.getLogger('root')
    logger.info('use commanding interface to configure tsh')


def fake_query_tsh_sample_rate(tsh_id):
    """probably gonna be part of more extensive get/fetch or class definition"""
    if tsh_id == 'tshes-44':
        return 250.0
    else:
        raise Exception('using fake query/get/fetch -- so only a fake, tshes-44, works')
