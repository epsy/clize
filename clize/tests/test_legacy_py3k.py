# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from sigtools import modifiers
from clize import clize, errors

from clize.tests.test_legacy import OldInterfaceTests

#from tests import HelpTester

class AnnotationParams(OldInterfaceTests):
    def test_alias(self):
        @clize
        @modifiers.annotate(one='o')
        def fn(one=1):
            return one
        self.assertEqual(
            fn('fn', '-o', '2'),
            2
            )

    def test_position(self):
        @clize
        @modifiers.annotate(one=clize.POSITIONAL)
        def fn(one=1):
            return one
        self.assertEqual(
            fn('fn', '2'),
            2
            )

    def test_coerce(self):
        @clize
        @modifiers.annotate(one=float)
        def fn(one):
            return one
        self.assertEqual(
            fn('fn', '2.1'),
            2.1
            )

    def test_coerce_and_default(self):
        @clize
        @modifiers.annotate(one=float)
        def fn(one=1):
            return one
        self.assertEqual(
            fn('fn'),
            1
            )
        self.assertEqual(
            fn('fn', '--one', '2.1'),
            2.1
            )

    def test_multiple(self):
        @clize
        @modifiers.annotate(one=(float, clize.POSITIONAL))
        def fn(one=1):
            return one
        self.assertEqual(
            fn('fn', '2.1'),
            2.1
            )
        self.assertEqual(
            fn('fn'),
            1
            )

class AnnotationFailures(OldInterfaceTests):
    def test_coerce_twice(self):
        def test():
            @clize
            @modifiers.annotate(one=(float, int))
            def fn(one):
                raise NotImplementedError
            fn.signature
        self.assertRaises(ValueError, test)

    def test_alias_space(self):
        def test():
            @clize
            @modifiers.annotate(one='a b')
            def fn(one=1):
                raise NotImplementedError
            fn.signature
        self.assertRaises(ValueError, test)

    def test_unknown(self):
        def test():
            @clize
            @modifiers.annotate(one=1.0)
            def fn(one):
                raise NotImplementedError
            fn.signature
        self.assertRaises(ValueError, test)

class KwoargsParams(OldInterfaceTests):
    def test_kwoparam(self):
        @clize
        @modifiers.kwoargs('one')
        def fn(one):
            return one

        self.assertEqual(
            fn('fn', '--one=one'),
            'one'
            )

    def test_kwoparam_required(self):
        @clize
        @modifiers.kwoargs('one')
        def fn(one):
            raise NotImplementedError

        self.assertRaises(errors.MissingRequiredArguments, fn, 'fn')

    def test_kwoparam_optional(self):
        @clize
        @modifiers.kwoargs('one')
        def fn(one=1):
            return one
        self.assertEqual(
            fn('fn'),
            1
            )
        self.assertEqual(
            fn('fn', '--one', '2'),
            2
            )
        self.assertEqual(
            fn('fn', '--one=2'),
            2
            )

    def test_optional_pos(self):
        @clize.kwo
        def fn(one, two=2):
            return one, two
        self.assertEqual(
            fn('fn', '1'),
            ('1', 2)
            )
        self.assertEqual(
            fn('fn', '1', '3'),
            ('1', 3)
            )
