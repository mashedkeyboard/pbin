#!/usr/bin/env python

# local imports
import sanity

import bottle
import json


def run_cmd(conf, cache):
    '''
    Execute an administrative command.
    '''
    data = bottle.request.json
    admin_key = conf.get('bottle', 'admin_key')

    # Supported commands
    commands = {
            'blacklist_paste': _cmd_blacklist_paste,
            'bl': _cmd_blacklist_paste,
            'delete': _cmd_delete_paste,
            'whitelist_address': _cmd_whitelist_address,
            'wl': _cmd_whitelist_address}

    # Pre-flight checks
    err = None
    if not admin_key:
        err = 'No admin key configured.'
    elif not 'token' in data:
        err = 'No auth provided.'
    elif data['token'] != admin_key:
        err = 'Invalid auth.'
    elif 'cmd' not in data:
        err = 'No command provided.'
    elif data['cmd'] not in commands:
        err = 'Command not supported.'
    if err:
        return {'msg': err, 'status': 'error'}

    # Flight
    return commands[data['cmd']](cache, data)


def _cmd_blacklist_paste(cache, data):
    # Delete paste
    _cmd_delete_paste(cache, data)

    # Block address
    if sanity.blacklist_address(cache, bottle.request.environ.get('REMOTE_ADDR', 'undef').strip()):
        return {'msg': 'Address "{}" blacklisted; posts removed.'.format(addr), 'status': 'success'}
    return {'msg': 'unexpected error', 'status': 'error'}


def _cmd_delete_paste(cache, data):
    paste = data.get('paste')
    if not paste:
        return {'msg': 'No paste provided.', 'status': 'error'}
    paste_id = 'paste:{}'.format(data['paste'])

    # Find paste origin address
    paste = cache.get(paste_id)
    if not paste:
        return {'msg': 'Paste not found.', 'status': 'error'}
    addr = json.loads(paste)['origin_addr']

    # Remove paste
    cache.delete(paste_id)


def _cmd_whitelist_address(cache, data):
    addr = data.get('address')
    if not addr:
        return {'msg': 'No address provided.', 'status': 'error'}

    if sanity.whitelist_address(cache, addr):
        return {'msg': 'Address subnet white listed.', 'status': 'success'}
    return {'msg': 'unexpected error', 'status': 'error'}
