from functools import partial
import unittest

class Tests(unittest.TestCase):
    pass

def make_run_test(func, value, **kwargs):
    def _func(self):
        return func(self, *value, **kwargs)
    return _func

def build_sigtests(func, cls):
    members = {
            '_test_func': func,
        }
    for key, value in cls.__dict__.items():
        if key.startswith('test_') or key.startswith('_'):
            members[key] = value
        else:
            members['test_' + key] = make_run_test(func, value)
    return type(cls.__name__, (Tests, unittest.TestCase), members)

def testfunc(test_func):
    return partial(build_sigtests, test_func)
