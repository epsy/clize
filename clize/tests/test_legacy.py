# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import sys
import unittest
import warnings
from io import StringIO

from clize import clize, errors, runner, make_flag


class OldInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        warnings.filterwarnings('ignore', '.*clize', DeprecationWarning)

    @classmethod
    def tearDownClass(self):
        warnings.filters.pop(0)

class ParamTests(OldInterfaceTests):
    def test_pos(self):
        @clize
        def fn(one, two, three):
            return one, two, three
        self.assertEqual(
            fn('fn', "1", "2", "3"),
            ('1', '2', '3')
            )

    def test_kwargs(self):
        @clize
        def fn(one='1', two='2', three='3'):
            return one, two, three
        self.assertEqual(
            fn('fn', '--three=6', '--two', '4'),
            ('1', '4', '6')
            )

    def test_mixed(self):
        @clize
        def fn(one, two='2', three='3'):
            return one, two, three
        self.assertEqual(
            fn('fn', '--two', '4', '0'),
            ('0', '4', '3')
            )

    def test_catchall(self):
        @clize
        def fn(one, two='2', *rest):
            return one, two, rest
        self.assertEqual(
            fn('fn', '--two=4', '1', '2', '3', '4'),
            ('1', '4', ('2', '3', '4'))
            )

    def test_coerce(self):
        @clize
        def fn(one=1, two=2, three=False):
            return one, two, three
        self.assertEqual(
            fn('fn', '--one=0', '--two', '4', '--three'),
            (0, 4, True)
            )

    def test_explicit_coerce(self):
        @clize(coerce={'one': int, 'two': int})
        def fn(one, two):
            return one, two
        self.assertEqual(
            fn('fn', '1', '2'),
            (1, 2)
            )

    def test_extra(self):
        @clize
        def fn(*args):
            return args
        self.assertEqual(fn('fn'), ())
        self.assertEqual(fn('fn', '1'), ('1',))
        self.assertEqual(fn('fn', '1', '2'), ('1', '2'))

    def test_extra_required(self):
        @clize(require_excess=True)
        def fn(*args):
            return args
        self.assertRaises(errors.MissingRequiredArguments, fn, 'fn')
        self.assertEqual(fn('fn', '1'), ('1',))
        self.assertEqual(fn('fn', '1', '2'), ('1', '2'))

    def test_too_short(self):
        @clize
        def fn(one, two):
            raise NotImplementedError
        self.assertRaises(errors.MissingRequiredArguments, fn, 'fn', 'one')

    def test_too_long(self):
        @clize
        def fn(one, two):
            raise NotImplementedError
        self.assertRaises(errors.TooManyArguments, fn, 'fn', 'one', 'two', 'three')

    def test_missing_arg(self):
        @clize
        def fn(one='1', two='2'):
            raise NotImplementedError
        self.assertRaises(errors.MissingValue, fn, 'fn', '--one')

    def test_short_param(self):
        @clize(alias={'one': ('o',)})
        def fn(one='1'):
            return one
        self.assertEqual(fn('fn', '--one', '0'), '0')
        self.assertEqual(fn('fn', '-o', '0'), '0')

    def test_short_int_param(self):
        @clize(alias={'one': ('o',), 'two': ('t',), 'three': ('s',)})
        def fn(one=1, two=2, three=False):
            return one, two, three
        self.assertEqual(fn('fn', '--one', '0'), (0, 2, False))
        self.assertEqual(fn('fn', '-o', '0', '-t', '4', '-s'), (0, 4, True))
        self.assertEqual(fn('fn', '-o0t4s'), (0, 4, True))

    def test_force_posarg(self):
        @clize(force_positional=('one',))
        def fn(one=1):
            return one
        self.assertEqual(fn('fn', '0'), 0)

    def test_unknown_option(self):
        @clize
        def fn(one=1):
            raise NotImplementedError
        self.assertRaises(errors.UnknownOption, fn, 'fn', '--doesnotexist')

    def test_coerce_fail(self):
        @clize
        def fn(one=1):
            raise NotImplementedError
        self.assertRaises(errors.BadArgumentFormat, fn, 'fn', '--one=nan')

    def test_custom_coerc(self):
        def coerc(arg):
            return 42
        @clize(coerce={'one': coerc})
        def fn(one):
            return one
        self.assertEqual(fn('fn', 'spam'), 42)

    def test_custom_type_default(self):
        class FancyDefault(object):
            def __init__(self, arg):
                self.arg = arg
        @clize
        def fn(one=FancyDefault('ham')):
            return one
        ret = fn('fn')
        self.assertEqual(type(ret), FancyDefault)
        self.assertEqual(ret.arg, 'ham')
        ret = fn('fn', '--one=spam')
        self.assertEqual(type(ret), FancyDefault)
        self.assertEqual(ret.arg, 'spam')

    def test_ignore_kwargs(self):
        @clize
        def fn(abc, xyz=0, **kwargs):
            return abc, xyz, kwargs
        abc, xyz, kwargs = fn('fn', 'abc')
        self.assertEqual(abc, 'abc')
        self.assertEqual(xyz, 0)
        self.assertEqual(kwargs, {})

def run_group(functions, args):
    disp = runner.SubcommandDispatcher(functions)
    return disp.cli(*args)

class SubcommandTests(OldInterfaceTests):
    def test_pos(self):
        @clize
        def fn1(one, two):
            return one, two
        self.assertEqual(
            run_group((fn1,), ('group', 'fn1', 'one', 'two')),
            ('one', 'two')
            )

    def test_opt(self):
        @clize
        def fn1(one='1', two='2'):
            return one, two
        self.assertEqual(
            run_group((fn1,), ('group', 'fn1', '--one=one', '--two', 'two')),
            ('one', 'two')
            )

    def test_unknown_command(self):
        @clize
        def fn1():
            raise NotImplementedError
        self.assertRaises(
            errors.ArgumentError,
            run_group, (fn1,), ('group', 'unknown')
            )

    def test_no_command(self):
        @clize
        def fn1():
            raise NotImplementedError
        self.assertRaises(
            errors.ArgumentError,
            run_group, (fn1,), ('group',)
            )

    def test_opts_but_no_command(self):
        @clize
        def fn1():
            raise NotImplementedError
        self.assertRaises(
            errors.ArgumentError,
            run_group, (fn1,), ('group', '--opt')
            )

class MakeFlagTests(OldInterfaceTests):
    def run_cli(self, func, args):
        orig_out = sys.stdout
        orig_err = sys.stderr
        try:
            sys.stdout = out = StringIO()
            sys.stderr = err = StringIO()
            ret = func(*args)
        finally:
            sys.stdout = orig_out
            sys.stderr = orig_err
        return ret, out, err

    def test_version(self):
        def show_version(name, **kwargs):
            print('this is the version')
            return True

        @clize(
            extra=(
                    make_flag(
                        source=show_version,
                        names=('version', 'v'),
                        help="Show the version",
                    ),
                )
            )
        def fn():
            raise NotImplementedError
        ret, out, err = self.run_cli(fn, ['test', '--version'])
        self.assertEqual(out.getvalue(), 'this is the version\n')
        self.assertEqual(err.getvalue(), '')
        ret, out, err = self.run_cli(fn, ['test', '-v'])
        self.assertEqual(out.getvalue(), 'this is the version\n')
        self.assertEqual(err.getvalue(), '')

    def test_keepgoing(self):
        def extra(name, command, val, params):
            if check_xyz:
                self.assertEqual(params['xyz'], 'xyz')
            else:
                self.assertFalse('xyz' in params)
            params['added'] = 'added'

        @clize(
            extra=(
                    make_flag(
                        source=extra,
                        names=('extra',),
                    ),
                )
            )
        def fn(arg1, arg2, added='', xyz=''):
            self.assertEqual(arg1, 'arg1')
            self.assertEqual(arg2, 'arg2')
            self.assertEqual(xyz, 'xyz')
            self.assertEqual(added, 'added')
        check_xyz = True
        self.run_cli(fn, ['test', 'arg1', '--xyz', 'xyz', 'arg2', '--extra'])
        check_xyz = False
        ret, out, err = self.run_cli(
            fn, ['test', 'arg1', '--extra', 'arg2', '--xyz', 'xyz'])

    def test_flag(self):
        @clize(
            extra=(
                make_flag(
                    source='extra',
                    names=('extra',)
                    ),
                )
            )
        def fn(arg1, arg2, **kwargs):
            return arg1, arg2, kwargs
        arg1, arg2, kwargs = fn('test', 'arg1', '--extra', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': True})

    def test_opt(self):
        @clize(
            extra=(
                make_flag(
                    source='extra',
                    names=('extra',),
                    type=str,
                    takes_argument=1
                    ),
                )
            )
        def fn(arg1, arg2, **kwargs):
            return arg1, arg2, kwargs
        arg1, arg2, kwargs = fn('test', 'arg1', '--extra', 'extra', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 'extra'})

    def test_intopt(self):
        @clize(
            extra=(
                make_flag(
                    source='extra',
                    names=('extra', 'e'),
                    type=int,
                    takes_argument=1
                    ),
                )
            )
        def fn(arg1, arg2, **kwargs):
            return arg1, arg2, kwargs
        arg1, arg2, kwargs = fn('test', 'arg1', '--extra', '42', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 42})
        arg1, arg2, kwargs = fn('test', 'arg1', '-e42', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 42})

    def test_moreargs(self):
        @clize(
            extra=(
                make_flag(
                    source='extra',
                    names=('extra', 'e'),
                    type=str,
                    takes_argument=3
                    ),
                )
            )
        def fn(arg1, arg2, **kwargs):
            return arg1, arg2, kwargs
        arg1, arg2, kwargs = fn(
            'test', 'arg1', '--extra', 'extra1', 'extra2', 'extra3', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 'extra1 extra2 extra3'})
        arg1, arg2, kwargs = fn(
            'test', 'arg1', '-e', 'extra1', 'extra2', 'extra3', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 'extra1 extra2 extra3'})
        arg1, arg2, kwargs = fn('test', 'arg1', '--extra=extra', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 'extra'})
        arg1, arg2, kwargs = fn('test', 'arg1', '-eextra', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 'extra'})
        self.assertRaises(errors.NotEnoughValues,
                          fn, 'test', 'arg1', 'arg2', '--extra', 'extra')

    def test_intopt_moreargs(self):
        @clize(
            extra=(
                make_flag(
                    source='extra',
                    names=('extra', 'e'),
                    type=int,
                    takes_argument=2
                    ),
                )
            )
        def fn(arg1, arg2, **kwargs):
            return arg1, arg2, kwargs
        arg1, arg2, kwargs = fn('test', 'arg1', '-e42', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 42})
        arg1, arg2, kwargs = fn('test', 'arg1', '--extra=42', 'arg2')
        self.assertEqual(arg1, 'arg1')
        self.assertEqual(arg2, 'arg2')
        self.assertEqual(kwargs, {'extra': 42})
        self.assertRaises(errors.BadArgumentFormat,
                          fn, 'test', '-e', 'extra1', 'extra2')
        self.assertRaises(errors.BadArgumentFormat,
                          fn, 'test', '--extra', 'extra1', 'extra2')
