"""Warm Python text helpers matching the RF2 generic text package contract.

No CLI, report, HTML renderer or MCP application entry is supplied here.
"""
import os
import re
import stat


def read_regular(path, limit=1048576):
    if type(limit) is not int or not 0 <= limit <= 1048576:
        raise ValueError('read bound')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('regular file required')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError('file byte limit')
        return data
    finally:
        os.close(descriptor)


def measure(data):
    if type(data) is not bytes or len(data) > 1048576:
        raise ValueError('text byte limit')
    text = data.decode('utf-8', 'strict')
    if any(ord(c) < 32 and c not in '\t\r\n' for c in text):
        raise ValueError('invalid text control')
    return dict(scalars=len(text), lines=data.count(b'\n') + int(bool(data) and not data.endswith(b'\n')),
                words_ascii_breaks=len(re.findall(rb'[^\t\r\n ]+', data)))


def search(data, query):
    if type(query) is not bytes or not 1 <= len(query) <= 128:
        raise ValueError('query byte limit')
    measure(query)
    count, first, pos = 0, None, 0
    while True:
        found = data.find(query, pos)
        if found < 0:
            return dict(matches=count, first_byte=first)
        if first is None:
            first = found
        count += 1
        pos = found + 1
