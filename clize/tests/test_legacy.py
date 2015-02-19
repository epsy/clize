#!/usr/bin/python
# encoding: utf-8
# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.


import unittest
import warnings

from clize import clize, errors, runner

class OldInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        warnings.filterwarnings('ignore', 'Use clize\.Clize',
                                DeprecationWarning)

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

