#!/usr/bin/python

import unittest

from clize import clize, errors

#from tests import HelpTester

class AnnotationParams(unittest.TestCase):
    def test_alias(self):
        @clize
        def fn(one: 'o' = 1):
            return one
        self.assertEqual(
            fn('fn', '-o', '2'),
            2
            )

    def test_position(self):
        @clize
        def fn(one: clize.POSITIONAL = 1):
            return one
        self.assertEqual(
            fn('fn', '2'),
            2
            )

    def test_coerce(self):
        @clize
        def fn(one: float):
            return one
        self.assertEqual(
            fn('fn', '2.1'),
            2.1
            )

    def test_coerce_and_default(self):
        @clize
        def fn(one: float = 1):
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
        def fn(one: (float, clize.POSITIONAL) = 1):
            return one
        self.assertEqual(
            fn('fn', '2.1'),
            2.1
            )
        self.assertEqual(
            fn('fn'),
            1
            )

class AnnotationFailures(unittest.TestCase):
    def test_coerce_twice(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: (float, int)):
                return one
            fn.signature

    def test_alias_space(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: 'a b'=1):
                return one
            fn.signature

    def test_unknown(self):
        with self.assertRaises(TypeError):
            @clize
            def fn(one: 1.0):
                return one
            fn.signature

class KwoargsParams(unittest.TestCase):
    def test_kwoparam(self):
        @clize
        def fn(*, one):
            return one

        self.assertEqual(
            fn('fn', '--one=one'),
            'one'
            )

    def test_kwoparam_required(self):
        @clize
        def fn(*, one):
            return one

        with self.assertRaises(errors.MissingRequiredArguments):
            fn('fn')

    def test_kwoparam_optional(self):
        @clize
        def fn(*, one=1):
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

class KwoargsHelpTests(object):
    def test_kwoparam(self):
        def fn(*, one='1'):
            """

            one: one!
            """
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] 

Options:
  --one=STR   one!(default: 1)
""")

    def test_kwoparam_required(self):
        def fn(*, one):
            """
            one: one!
            """
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] 

Options:
  --one=STR   one!(required)
""") # ಠ_ಠ
