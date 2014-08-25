from functools import partial
import unittest

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
