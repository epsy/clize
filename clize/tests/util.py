# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from functools import partial
import unittest

from six.moves import cStringIO

from clize import runner


class Tests(unittest.TestCase):
    def assertRaises(self, _exc, _func, *args, **kwargs):
        try:
            _func(*args, **kwargs)
        except _exc:
            pass
        else:
            self.fail("{0} did not raise {1}".format(_func, _exc))
    if hasattr(unittest.TestCase, 'assertRaises'):
        del assertRaises


def make_run_test(func, value, **kwargs):
    def _func(self):
        return func(self, *value, **kwargs)
    return _func

def build_sigtests(func, cls):
    if func is None:
        func = cls.__dict__['_test_func']
    members = {
            '_test_func': func,
        }
    for key, value in cls.__dict__.items():
        members[key] = value
        if not key.startswith('test_') and not key.startswith('_'):
            members['test_' + key] = make_run_test(func, value)
    return type(cls.__name__, (Tests, unittest.TestCase), members)

def testfunc(test_func):
    return partial(build_sigtests, test_func)

repeated_test = partial(build_sigtests, None)


def read_arguments(sig, args):
    return sig.read_arguments(args, 'test')


def run(func, args, **kwargs):
    stdout = cStringIO()
    stderr = cStringIO()
    runner.run(func, args=args, exit=False, out=stdout, err=stderr, **kwargs)
    return stdout, stderr
