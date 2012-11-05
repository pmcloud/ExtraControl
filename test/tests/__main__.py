#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils

from case.sanity import *
from case.modulemng import *
from case.execute import *
from case.upload import *
from case.remove import *
from case.updatemodule import *
from case.netconf import *
from case.osinfo import *
from case.systemstatus import *
from case.module_lifecycle import *

# later tests rely on the ability to load/list/remove module; tests not
# listed here will be executed last
TEST_ORDER = [
    'case.sanity',
    'case.modulemng',
    'case.upload',
    'case.remove',
]


# use test order above
def load_tests(loader, tests, pattern):
    def first(it):
        for i in it:
            return i

    def key(suite):
        test = first(suite)

        try:
            return TEST_ORDER.index(test.__module__)
        except:
            return 10000

    return tests.__class__(list(sorted(tests, key=key)))


utils.main()
