#!/usr/bin/python3

"""
Fake iscriptevaluator.exe
"""
import os
import re
import subprocess
import urllib.request
import shutil

import tweaks
import xdg

import toolbox

from log import log

STEAM_APP_ID = os.environ.get('SteamAppId', '0')

PID_FILE = '/tmp/roberta_{0}'.format(STEAM_APP_ID)


def wait_for_previous_process():
    """Wait for other process to end."""
    pid = 0
    try:
        with open(PID_FILE, 'r') as pid_file:
            pid = int(pid_file.read())
    except FileNotFoundError:
        pass
    if pid and os.path.isfile('/proc/{0}/cmdline'.format(pid)):
        log('waiting for process', pid, 'to stop and delete file', PID_FILE)
        subprocess.call(['inotifywait', '-e', 'delete', PID_FILE])


def download_item(i, num, name, desc):
    """Download a file to cache."""
    txt = desc['txt']
    url = desc['url']
    cache_file = xdg.cached_file(name)
    if os.path.isfile(cache_file):
        return
    log('downloading', url, 'to', cache_file)
    msg = '{}/{}: {}'.format(i, num, txt)
    # TODO use runtime dir instead of cache here
    with open(xdg.cached_file('desc.txt'), 'w') as msg_file:
        msg_file.write(msg)
    with urllib.request.urlopen(url) as resp, open(cache_file, 'wb') as out:
        shutil.copyfileobj(resp, out)


def print_current_step():
    """Print description of current 'installation' step."""
    # leaving message in a file is not the most sophisticated solution
    # works for now; maybe replace with FIFO later, if needed
    msg_path = xdg.cached_file('desc.txt')
    if not os.path.isfile(msg_path):
        return
    with open(msg_path, 'r') as msg_file:
        msg = msg_file.read().strip()
        print(msg, end='')


def iscriptevaluator(args):
    """Pretend to be iscriptevaluator.exe program."""
    assert args
    last_arg = args[-1]

    if '--get-current-step' in args:
        # steam_app_id = last_arg
        print_current_step()
        return 0

    # STEAM_APP_ID is 0 during installation
    steam_app_id = 0
    script_name_pattern = re.compile(r'.*script_(\d+)\.vdf')
    match = script_name_pattern.match(last_arg)
    if match:
        steam_app_id = match.group(1)

    if not tweaks.download_tweak_needed(steam_app_id):
        return 0

    download_links = tweaks.TWEAKS_DB[steam_app_id]['download']
    num = len(download_links)
    pid_file = '/tmp/roberta_{0}'.format(steam_app_id)
    i = 0
    with toolbox.PidFile(pid_file):
        for name, desc in download_links.items():
            download_item(i, num, name, desc)
            i += 1
    try:
        os.remove(xdg.cached_file('desc.txt'))
    except FileNotFoundError:
        pass

    status = 0
    return status
