# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import pathlib
import sys
import unittest
from io import StringIO

import repeated_test
from repeated_test import options

from clize import runner, errors
from clize.tests.util import Fixtures, Tests


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


class ModuleNameTests(Fixtures):
    def _test(self, filename, name, package, result):
        module = MockModule(filename, name, package)
        self.assertEqual(result, runner.main_module_name(module))

    if sys.version_info < (2,7):
        _dmainret = 'pack.__main__'
    else:
        _dmainret = 'pack'
    dunder_main = sp+'pack/__main__.py', '__main__', 'pack', _dmainret
    free_module = sp+'free.py', '__main__', '', 'free'
    submodule = sp+'pack/sub.py', '__main__', 'pack', 'pack.sub'

    def test_pudb_script(self):
        module = BadModule(sp+'pack/cli.py', '__main__')
        self.assertEqual(None, runner.main_module_name(module))


@repeated_test.with_options_matrix(
    to_path=[pathlib.PurePosixPath, pathlib.PureWindowsPath]
)
class GetExecutableTests(Fixtures):
    def _test(self, path, expected, *, which=None, to_path):
        def which_(name):
            if which:
                return str(to_path(which, name))
            else:
                return None
        ret = runner._get_executable(path, which=which_, to_path=to_path)
        self.assertEqual(ret, expected)

    none = None, None
    empty = '', None

    with options(to_path=pathlib.PurePosixPath):
        posix_dotpy = '/a/path/leading/to/myapp.py', '/a/path/leading/to/myapp.py'
        posix_in_path = '/usr/bin/myapp', 'myapp', options(which='/usr/bin')
        posix_not_in_path = '/opt/myapp/bin/myapp', '/opt/myapp/bin/myapp'
        posix_not_from_path = '/opt/myapp/bin/myapp', '/opt/myapp/bin/myapp', options(which='/usr/bin')
        posix_relpath = 'myapp/bin/myapp', 'myapp/bin/myapp', options(which='')
        posix_parentpath_also_in_path = '../myapp/bin/myapp', '../myapp/bin/myapp', options(which='')
        posix_parentpath = '../myapp/bin/myapp', '../myapp/bin/myapp', options(which=None)

    with options(to_path=pathlib.PureWindowsPath):
        win_dotpy = "C:/a/path/leading/to/myapp.py", r"C:\a\path\leading\to\myapp.py"
        win_in_path = 'C:/Program Files/myapp/bin/myapp.py', 'myapp.py', options(which='C:/Program Files/myapp/bin/')
        win_not_in_path = 'C:/Users/Myself/Documents/myapp', r'C:\Users\Myself\Documents\myapp'
        win_not_from_path = 'C:/Users/Myself/Documents/myapp', r'C:\Users\Myself\Documents\myapp', options(which='C:/system32')
        win_relpath = './my/folder/myapp.py', r'my\folder\myapp.py', options(which=None)
        win_parentpath_also_in_path = '../myapp/bin/myapp', r'..\myapp\bin\myapp', options(which='')
        win_parentpath = '../myapp/bin/myapp', r'..\myapp\bin\myapp', options(which=None)
        win_diff_drives = 'D:/myapp/bin/myapp', r"D:\myapp\bin\myapp", options(which="C:/myapp/bin/myapp")


def get_executable_verbatim(path):
    return path


@repeated_test.with_options_matrix(platform=["anythingreally", "win32"], executable=["interpreter"], get_executable=[get_executable_verbatim])
class FixArgvTests(Fixtures):
    def _test(self, argv, path, main, expect, *, platform, executable, get_executable):
        module = MockModule(*main)
        self.assertEqual(expect, runner._fix_argv(argv, path, module, executable=executable, platform=platform, get_executable=get_executable))

    plainfile = (
        ['afile.py', '...'], ['/path/to/cwd', '/usr/lib/pythonX.Y'],
        ['afile.py', '__main__', None],
        ['afile.py', '...'],
        options(platform="anythingreally"),
    )

    plainfile_win = (
        ['afile.py', '...'], ['/path/to/cwd', '/usr/lib/pythonX.Y'],
        ['afile.py', '__main__', None],
        ['interpreter afile.py', '...'],
        options(platform="win32"),
    )

    asmodule = (
        ['/path/to/cwd/afile.py', '...'], ['', '/usr/lib/pythonX.Y'],
        ['/path/to/cwd/afile.py', '__main__', ''],
        ['interpreter -m afile', '...']
        )
    packedmodule = (
        ['/path/to/cwd/apkg/afile.py', '...'], ['', '/usr/lib/pythonX.Y'],
        ['/path/to/cwd/apkg/afile.py', '__main__', 'apkg'],
        ['interpreter -m apkg.afile', '...']
        )
    packedmain2 = (
        ['/path/to/cwd/apkg/__main__.py', '...'], ['', '/usr/lib/pythonX.Y'],
        ['/path/to/cwd/apkg/__main__.py', 'apkg.__main__', 'apkg'],
        ['interpreter -m apkg', '...']
        )
    packedmain3 = (
        ['/path/to/cwd/apkg/__main__.py', '...'], ['', '/usr/lib/pythonX.Y'],
        ['/path/to/cwd/apkg/__main__.py', '__main__', 'apkg'],
        ['interpreter -m apkg', '...']
        )

    def test_bad_fakemodule(self):
        module = BadModule('/path/to/cwd/afile.py', '__main__')
        argv = ['afile.py', '...']
        path = ['', '/usr/lib/pythonX.Y']
        self.assertEqual(['afile.py', '...'],
                         runner._fix_argv(argv, path, module, get_executable=lambda p: ''))


class GetCliTests(unittest.TestCase):
    def test_simple(self):
        def func():
            raise NotImplementedError
        ru = runner.Clize.get_cli(func)
        self.assertTrue(isinstance(ru, runner.Clize))
        self.assertTrue(ru.func is func)

    def test_cliattr(self):
        def func():
            raise NotImplementedError
        func.cli = object()
        ru = runner.Clize.get_cli(func)
        repr(ru)
        self.assertTrue(ru is func.cli)

    def test_sub_ita(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        ru = runner.Clize.get_cli(iter([func1, func2]))
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        self.assertEqual(sd.cmds_by_name['func1'].func, func1)
        self.assertEqual(sd.cmds_by_name['func2'].func, func2)

    def test_sub_dict(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        ru = runner.Clize.get_cli({'abc': func1, 'def': func2})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 2)
        self.assertEqual(sd.cmds_by_name['abc'].func, func1)
        self.assertEqual(sd.cmds_by_name['def'].func, func2)

    def test_sub_dict_extra_names(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        ru = runner.Clize.get_cli({('abc', 'ghi'): func1, 'def': func2})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 3)
        self.assertEqual(len(sd.cmds), 2)
        self.assertEqual(sd.cmds_by_name['abc'].func, func1)
        self.assertEqual(sd.cmds_by_name['def'].func, func2)
        self.assertEqual(sd.cmds_by_name['ghi'].func, func1)

    def test_sub_dict_repeat_values(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        ru = runner.Clize.get_cli({'abc': func1, 'def': func2, 'ghi': func1})
        repr(ru)
        sd = ru.func.__self__
        self.assertTrue(isinstance(sd,
                                   runner.SubcommandDispatcher))
        self.assertEqual(len(sd.cmds_by_name), 3)
        self.assertEqual(len(sd.cmds), 2)
        self.assertEqual(sd.cmds_by_name['abc'].func, func1)
        self.assertEqual(sd.cmds_by_name['def'].func, func2)

    def test_sub_alt(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        def alt(): raise NotImplementedError
        ru = runner.Clize.get_cli([func1, func2], alt=alt)
        sub, name, args, kwargs = ru.read_commandline(['test', '--alt'])
        self.assertTrue(sub.func is alt)

    def test_nested_ita_error(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        def func3(): raise NotImplementedError
        def func4(): raise NotImplementedError
        self.assertRaises(
            ValueError,
            runner.Clize.get_cli,
            iter([iter([func1, func2]), iter([func3, func4])]))

    def test_nested_dict_ita(self):
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        def func3(): raise NotImplementedError
        def func4(): raise NotImplementedError
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
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        def func3(): raise NotImplementedError
        def func4(): raise NotImplementedError
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
        def func1(): raise NotImplementedError
        def func2(): raise NotImplementedError
        def func3(): raise NotImplementedError
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
        def func(): raise NotImplementedError
        ru = runner.Clize.get_cli(runner.Clize.as_is(func))
        repr(ru)
        self.assertEqual(ru, func)

    def test_as_is_desc(self):
        def func(): raise NotImplementedError
        ru = runner.Clize.get_cli(runner.Clize.as_is(func, description="desc"))
        repr(ru)
        self.assertEqual(ru, func)

    def test_as_is_desc_deco(self):
        def func(): raise NotImplementedError
        clio = runner.Clize.as_is(description="desc")(func)
        ru = runner.Clize.get_cli(clio)
        repr(ru)
        self.assertEqual(ru, func)

    def test_as_is_usage(self):
        def func(): raise NotImplementedError
        clio = runner.Clize.as_is(usages=['ua'])(func)
        ru = runner.Clize.get_cli(clio)
        repr(ru)
        self.assertEqual(ru, func)

    def test_as_is_usage_desc(self):
        def func(): raise NotImplementedError
        clio = runner.Clize.as_is(
            usages=['ua'], description="desc")(func)
        ru = runner.Clize.get_cli(clio)
        repr(ru)
        self.assertEqual(ru, func)

    def test_keep(self):
        def func(): raise NotImplementedError
        c = runner.Clize.keep(func)
        ru = runner.Clize.get_cli(c)
        repr(ru)
        self.assertTrue(c is func)
        self.assertTrue(isinstance(c.cli, runner.Clize))
        self.assertTrue(c.cli.func is func)
        self.assertTrue(ru.func is func)

    def test_keep_args(self):
        def func(): raise NotImplementedError
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
        def func(): raise NotImplementedError
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

class RunnerTests(Tests):
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

    def test_subcommand_error(self):
        def snake_case():
            raise NotImplementedError
        def CamelCase():
            raise NotImplementedError
        ru = runner.Clize.get_cli([snake_case, CamelCase])
        message = (
            'test: Unknown command "CamelCase"\\. Did you mean "camel-case"\\?'
            '\nUsage: test command \\[args\\.\\.\\.\\]')
        with self.assertRaisesRegex(errors.ArgumentError, message):
            ru('test', 'CamelCase')

    def assert_systemexit(self, __code, __func, *args, **kwargs):
        try:
            __func(*args, **kwargs)
        except SystemExit as e:
            try:
                self.assertEqual(e.code, __code)
            except AssertionError:
                if not (e.code == 0 and __code is None):
                    raise
        else:
            self.fail('SystemExit not raised')

    def test_assert_systemexit(self):
        def raiseSysexitIfArg(arg):
            if arg:
                sys.exit()
        self.assert_systemexit(None, raiseSysexitIfArg, True)
        raiseSysexitIfArg(False)
        self.assertRaises(
            AssertionError, self.assert_systemexit, None,
            raiseSysexitIfArg, False)
        def raiseSysexitWithCode():
            sys.exit(2)
        self.assert_systemexit(2, raiseSysexitWithCode)
        self.assertRaises(
            AssertionError, self.assert_systemexit, 1, raiseSysexitWithCode)

    def test_run_fail_exit(self):
        def func():
            raise errors.ArgumentError("test_run_fail_exit")
        stdout = StringIO()
        stderr = StringIO()
        self.assert_systemexit(
            2, runner.run, func, args=['test'], out=stdout, err=stderr)
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue())
        runner.run(func, args=['test'], out=stdout, err=stderr, exit=False)

    def test_run_success_exit(self):
        def func():
            return "test_run_success_exit"
        stdout = StringIO()
        stderr = StringIO()
        self.assert_systemexit(
            None, runner.run, func, args=['test'], out=stdout, err=stderr)
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), 'test_run_success_exit\n')
        runner.run(func, args=['test'], out=stdout, err=stderr, exit=False)

    def test_run_silent(self):
        def func():
            pass
        stdout, stderr = self.crun(func, args=['test'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())

    def test_run_multi(self):
        def func1(): return '1'
        def func2(): return '2'
        stdout, stderr = self.crun([func1, func2], args=['test', 'func1'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout, stderr = self.crun([func1, func2], args=['test', 'func2'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '2\n')
        stdout = StringIO()
        stderr = StringIO()
        runner.run(func1, func2, args=['test', 'func1'],
                   out=stdout, err=stderr, exit=False)
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')

    def test_alt(self):
        def func1(): return '1'
        def func2(): return '2'
        stdout, stderr = self.crun(func1, alt=func2, args=['test'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout, stderr = self.crun(func1, alt=func2, args=['test', '--func2'])
        self.assertFalse(stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '2\n')

    def test_disable_help(self):
        def func1(): raise NotImplementedError
        stdout, stderr = self.crun(
            func1, help_names=[], args=['test', '--help'])
        self.assertTrue(stderr.getvalue())
        self.assertFalse(stdout.getvalue())

    def test_run_sysargv(self):
        bmodules = sys.modules
        bargv = sys.argv
        bpath = sys.path
        try:
            sys.modules['__main__'] \
                = MockModule('/path/to/cwd/afile.py', '__main__', '')
            sys.argv = ['afile.py', '...']
            sys.path = [''] + sys.path[1:]
            def func(arg=1):
                raise NotImplementedError
            out = StringIO()
            err = StringIO()
            runner.run(func, exit=False, out=out, err=err)
            self.assertFalse(out.getvalue())
            self.assertRegex(err.getvalue(),
                ".* -m afile: Bad value for arg: '...'\n"
                r"Usage: .* -m afile \[arg\]" "\n")
        finally:
            sys.modules = bmodules
            sys.argv = bargv
            sys.path = bpath

    def test_run_out(self):
        bout = sys.stdout
        try:
            sys.stdout = out = StringIO()
            def func():
                return 'hello'
            runner.run(func, args=['test'], exit=False)
            self.assertEqual(out.getvalue(), 'hello\n')
        finally:
            sys.stdout = bout

    def test_run_err(self):
        berr = sys.stderr
        try:
            sys.stderr = err = StringIO()
            def func(arg=1):
                raise NotImplementedError
            runner.run(func, args=['test', '...'], exit=False)
            self.assertEqual(err.getvalue(),
                "test: Bad value for arg: '...'\n"
                "Usage: test [arg]\n")
        finally:
            sys.stderr = berr

    def test_catch_usererror(self):
        def func():
            raise errors.UserError('test_catch_usererror')
        out, err = self.crun(func, ['test'])
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'test: test_catch_usererror\n')

    def test_catch_argumenterror(self):
        def func():
            raise errors.ArgumentError('test_catch_argumenterror')
        out, err = self.crun(func, ['test'])
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'test: test_catch_argumenterror\n'
                                         'Usage: test\n')

    def test_catch_customerror(self):
        class MyError(Exception):
            pass
        def func():
            raise MyError('test_catch_customerror')
        out, err = self.crun(func, ['test'], catch=[MyError])
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'test_catch_customerror\n')

    def test_catch_argerror_cust(self):
        class MyError(Exception):
            pass
        def func():
            raise errors.UserError('test_catch_argerror_cust')
        out, err = self.crun(func, ['test'], catch=[MyError])
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'test: test_catch_argerror_cust\n')
