import os
import sys
import shutil

from clize.tests import util
from clize import runner


class MockModule(object):
    def __init__(self, filename, name, package):
        self.__file__ = filename
        self.__name__ = name
        self.__package__ = package


class BadModule(MockModule):
    def __init__(self, *args, **kwargs):
        super(BadModule, self).__init__(*args, package=None, **kwargs)
        del self.__package__


sp = '/usr/lib/python3.4/site-packages/'


@util.repeated_test
class ModuleNameTests(object):
    def _test_func(self, filename, name, package, result):
        module = MockModule(filename, name, package)
        self.assertEqual(result, runner.main_module_name(module))

    if sys.version_info >= (2,7):
        _dmainret = 'pack'
    else:
        _dmainret = 'pack.__main__'
    dunder_main = sp+'pack/__main__.py', '__main__', 'pack', _dmainret
    free_module = sp+'free.py', '__main__', '', 'free'
    submodule = sp+'pack/sub.py', '__main__', 'pack', 'pack.sub'

    def test_pudb_script(self):
        module = BadModule(sp+'pack/cli.py', '__main__')
        self.assertRaises(AttributeError, runner.main_module_name, module)

@util.repeated_test
class GetExcecutableTests(object):
    def _test_func(self, path, default, result, which='/usr/bin'):
        which_backup = getattr(shutil, 'which', None)
        def which_(name, *args, **kwargs):
            if which:
                return os.path.join('/usr/bin', name)
            else:
                return None
        shutil.which = which_
        if which is None:
            del shutil.which
        try:
            ret = runner.get_executable(path, default)
            self.assertEqual(ret, result)
        finally:
            if which_backup:
                shutil.which = which_backup
            elif which is not None:
                del shutil.which

    none = None, 'python', 'python'
    empty = '', 'myapp', 'myapp'
    dotpy = '/a/path/leading/to/myapp.py', None, '/a/path/leading/to/myapp.py'
    in_path = '/usr/bin/myapp', None, 'myapp'
    in_path_2 = '/usr/bin/myapp', None, 'myapp', None
    not_in_path = '/opt/myapp/bin/myapp', None, '/opt/myapp/bin/myapp'
    relpath = 'myapp/bin/myapp', None, 'myapp/bin/myapp', ''
    parentpath = '../myapp/bin/myapp', None, '../myapp/bin/myapp', ''
    parentpath_2 = '../myapp/bin/myapp', None, '../myapp/bin/myapp', None
