#!/usr/bin/python

import unittest

from clize import clize, ArgumentError

from tests import HelpTester

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
    def test_coerce(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: (float, int)):
                return one
            fn()

    def test_alias(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: 'a b'):
                return one
            fn()

    def test_unknown(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: 1.0):
                return one
            fn()

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

        self.assertRaisesRegexp(
            ArgumentError,
            r"Missing required option --one.\nUsage: fn \[OPTIONS\] ",
            fn, 'fn'
            )

    def test_kwoparam_optional(self):
        @clize
        def fn(*, one=1):
            return one
        self.assertEquals(
            fn('fn'),
            1
            )
        self.assertEquals(
            fn('fn', '--one', '2'),
            2
            )
        self.assertEquals(
            fn('fn', '--one=2'),
            2
            )

    def test_optional_pos(self):
        @clize.kwo
        def fn(one, two=2):
            return one, two
        self.assertEquals(
            fn('fn', '1'),
            ('1', 2)
            )
        self.assertEquals(
            fn('fn', '1', '3'),
            ('1', 3)
            )

class KwoargsHelpTests(HelpTester):
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

if __name__ == '__main__':
    unittest.main()
