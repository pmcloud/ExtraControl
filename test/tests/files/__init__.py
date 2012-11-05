#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

WINDOWS = os.path.join(os.path.dirname(__file__), 'windows')
LINUX = os.path.join(os.path.dirname(__file__), 'linux')
MODULE = os.path.join(os.path.dirname(__file__), 'module')


def windows(*parts):
    return os.path.join(WINDOWS, *parts)


def linux(*parts):
    return os.path.join(LINUX, *parts)


def module(*parts):
    return os.path.join(MODULE, *parts)


def executable(is_windows, name):
    if is_windows:
        path = windows(name + '.bat')
    else:
        path = linux(name)

    return file(path).read()
