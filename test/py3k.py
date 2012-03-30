#!/usr/bin/python

import unittest
from clize import clize


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

    def test_alias(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: 'a b'):
                return one

    def test_unknown(self):
        with self.assertRaises(ValueError):
            @clize
            def fn(one: 1.0):
                return one


if __name__ == '__main__':
    unittest.main()
