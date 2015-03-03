# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import os
import sys
import shutil
import unittest

from six.moves import cStringIO

from clize.tests import util
from clize import runner, errors


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

@util.repeated_test
class FixArgvTests(object):
    def _test_func(self, argv, path, main, expect):
        module = MockModule(*main)
        self.assertEqual(expect, runner.fix_argv(argv, path, module))


class GetCliTests(unittest.TestCase):
    def test_simple(self):
        def func():
            pass
        ru = runner.Clize.get_cli(func)
        self.assertTrue(isinstance(ru, runner.Clize))
        self.assertTrue(ru.func is func)

    def test_cliattr(self):
        def func():
            pass
        func.cli = object()
        ru = runner.Clize.get_cli(func)
        repr(ru)
        self.assertTrue(ru is func.cli)

    def test_sub_ita(self):
        def func1(): pass
        def func2(): pass
        ru = runner.Clize.get_cli(iter([func1, func2]))
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        self.assertEqual(sd.cmds_by_name['func1'].func, func1)
        self.assertEqual(sd.cmds_by_name['func2'].func, func2)

    def test_sub_dict(self):
        def func1(): pass
        def func2(): pass
        ru = runner.Clize.get_cli({'abc': func1, 'def': func2})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        self.assertEqual(sd.cmds_by_name['abc'].func, func1)
        self.assertEqual(sd.cmds_by_name['def'].func, func2)

    def test_nested_ita_error(self):
        def func1(): pass
        def func2(): pass
        def func3(): pass
        def func4(): pass
        try:
            runner.Clize.get_cli(
                iter([iter([func1, func2]), iter([func3, func4])]))
        except ValueError:
            pass
        else:
            self.fail("AttributeError not raised")

    def test_nested_dict_ita(self):
        def func1(): pass
        def func2(): pass
        def func3(): pass
        def func4(): pass
        ru = runner.Clize.get_cli(
            {'gr1': iter([func1, func2]), 'gr2': iter([func3, func4])})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        sd1 = sd.cmds_by_name['gr1'].func.__self__
        sd2 = sd.cmds_by_name['gr2'].func.__self__
        self.assertEqual(sd1.cmds_by_name['func1'].func, func1)
        self.assertEqual(sd1.cmds_by_name['func2'].func, func2)
        self.assertEqual(sd2.cmds_by_name['func3'].func, func3)
        self.assertEqual(sd2.cmds_by_name['func4'].func, func4)

    def test_nested_dict_dict(self):
        def func1(): pass
        def func2(): pass
        def func3(): pass
        def func4(): pass
        ru = runner.Clize.get_cli(
            {'gr1': {'a': func1, 'b': func2},
             'gr2': {'c': func3, 'd' : func4}})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        sd1 = sd.cmds_by_name['gr1'].func.__self__
        sd2 = sd.cmds_by_name['gr2'].func.__self__
        self.assertEqual(sd1.cmds_by_name['a'].func, func1)
        self.assertEqual(sd1.cmds_by_name['b'].func, func2)
        self.assertEqual(sd2.cmds_by_name['c'].func, func3)
        self.assertEqual(sd2.cmds_by_name['d'].func, func4)

    def test_sub_empty_key(self):
        def func1(): pass
        def func2(): pass
        def func3(): pass
        ru = runner.Clize.get_cli({
                '': func1,
                '2': func2,
                '3': func3,
            })
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(set(sd.cmds_by_name), set(['2', '3']))

    def test_as_is(self):
        def func(): pass
        ru = runner.Clize.get_cli(runner.Clize.as_is(func))
        repr(ru)
        self.assertEqual(ru, func)

    def test_keep(self):
        def func(): pass
        c = runner.Clize.keep(func)
        ru = runner.Clize.get_cli(c)
        repr(ru)
        self.assertTrue(c is func)
        self.assertTrue(isinstance(c.cli, runner.Clize))
        self.assertTrue(c.cli.func is func)
        self.assertTrue(ru.func is func)

    def test_keep_args(self):
        def func(): pass
        c = runner.Clize.keep(hide_help=True)(func)
        ru = runner.Clize.get_cli(c)
        repr(ru)
        self.assertTrue(c is func)
        self.assertTrue(isinstance(c.cli, runner.Clize))
        self.assertTrue(c.cli.func is func)
        self.assertTrue(c.cli.hide_help)
        self.assertTrue(ru.func is func)

    def test_decorated(self):
        @runner.Clize
        def func(): pass
        ru = runner.Clize.get_cli(func)
        repr(ru)
        self.assertTrue(ru is func)

    def test_instattr(self):
        class Cls(object):
            def method(self):
                return 'instattr'
        inst = Cls()
        meth = inst.method
        ru = runner.Clize.get_cli(meth)
        repr(ru)
        self.assertTrue(ru.func is meth)
        self.assertEqual(ru('test'), 'instattr')

    def test_instattr_deco(self):
        class Cls(object):
            @runner.Clize
            def method(self):
                return 'instattr_deco'
        inst = Cls()
        ru = inst.method
        self.assertTrue(isinstance(ru, runner.Clize))
        self.assertEqual(ru('test'), 'instattr_deco')
        self.assertTrue(ru.owner is inst)
        repr(ru)

    def test_instattr_deco_selfget(self):
        class SelfGet(object):
            __name__ = 'SelfGet'
            def __get__(self, instance, owner):
                return self
        class Cls(object):
            method = runner.Clize(SelfGet())
        inst = Cls()
        ru = inst.method
        self.assertTrue(Cls.__dict__['method'] is ru)

    def test_instattr_deco_noget(self):
        class NoGet(object):
            __name__ = 'NoGet'
        class Cls(object):
            method = runner.Clize(NoGet())
        inst = Cls()
        ru = inst.method
        self.assertTrue(Cls.__dict__['method'] is ru)

    def test_unknown(self):
        obj = object()
        self.assertRaises(TypeError, runner.Clize.get_cli, obj)

class RunnerTests(unittest.TestCase):
    def test_subcommand(self):
        def func1(x):
            return x+' world'
        def func2():
            pass
        ru = runner.Clize.get_cli([func1, func2])
        self.assertEqual(ru('test', 'func1', 'hello'), 'hello world')
        self.assertEqual(ru('test', 'func2'), None)
        self.assertRaises(errors.ArgumentError, ru, 'test', 'func2', 'abc')
        self.assertRaises(errors.ArgumentError, ru, 'test', 'func3')

    def test_run_fail_exit(self):
        def func():
            raise errors.ArgumentError("test_run_fail_exit")
        stdout = cStringIO()
        stderr = cStringIO()
        try:
            runner.run(func, args=['test'], out=stdout, err=stderr)
        except SystemExit as e:
            self.assertEqual(e.code, 2)
        else:
            self.fail("ArgumentError not raised")
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue())
        runner.run(func, args=['test'], out=stdout, err=stderr, exit=False)

    def test_run_success_exit(self):
        def func():
            return "test_run_success_exit"
        stdout = cStringIO()
        stderr = cStringIO()
        try:
            runner.run(func, args=['test'], out=stdout, err=stderr)
        except SystemExit as e:
            self.assertFalse(e.code)
        else:
            self.fail("ArgumentError not raised")
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), 'test_run_success_exit\n')
        runner.run(func, args=['test'], out=stdout, err=stderr, exit=False)

    def test_run_silent(self):
        def func():
            pass
        stdout, stderr = util.run(func, args=['test'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())

    def test_run_multi(self):
        def func1(): return '1'
        def func2(): return '2'
        stdout, stderr = util.run([func1, func2], args=['test', 'func1'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout, stderr = util.run([func1, func2], args=['test', 'func2'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '2\n')
        stdout = cStringIO()
        stderr = cStringIO()
        runner.run(func1, func2, args=['test', 'func1'],
                   out=stdout, err=stderr, exit=False)
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')

    def test_alt(self):
        def func1(): return '1'
        def func2(): return '2'
        stdout, stderr = util.run(func1, alt=func2, args=['test'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout, stderr = util.run(func1, alt=func2, args=['test', '--func2'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '2\n')

    def test_disable_help(self):
        def func1(): return '1'
        stdout, stderr = util.run(
            func1, help_names=[], args=['test', '--help'])
        self.assertTrue(stderr.getvalue())
        self.assertFalse(stdout.getvalue())
