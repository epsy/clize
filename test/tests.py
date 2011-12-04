#!/usr/bin/python

import unittest
from clize import clize, ArgumentError, read_arguments, help

class ParamTests(unittest.TestCase):

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

    def test_too_short(self):
        @clize
        def fn(one, two):
            pass
        self.assertRaisesRegexp(
            ArgumentError,
            r"Not enough arguments.\nUsage: fn \[OPTIONS\] one two",
            fn, 'fn', 'one',
            )

    def test_too_long(self):
        @clize
        def fn(one, two):
            pass
        self.assertRaisesRegexp(
            ArgumentError,
            r"Too many arguments.\nUsage: fn \[OPTIONS\] one two",
            fn, 'fn', 'one', 'two', 'three'
            )

    def test_missing_arg(self):
        @clize
        def fn(one='1', two='2'):
            pass
        self.assertRaisesRegexp(
            ArgumentError,
            r"--one needs an argument.\nUsage: fn \[OPTIONS\]",
            fn, 'fn', '--one'
            )

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

    def test_coerce_fail(self):
        @clize(alias=())
        def fn():
            pass

class HelpTests(unittest.TestCase):

    def assertHelpEquals(
            self, fn, help_str,
            alias={}, force_positional=(),
            require_excess=False, coerce={}
            ):
        return self.assertEqual(
            help('fn',
                read_arguments(fn, alias, force_positional,
                               require_excess, coerce),
                do_print=False),
            help_str
            )

    def test_pos(self):
        def fn(one, two, three, *more):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn one two three [more...]

Positional arguments:
  one      
  two      
  three    
  more...  
""")

    def test_kwargs(self):
        def fn(one='1', two=2, three=3.0, four=False):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] 

Options:
  --one=STR      
  --two=INT      
  --three=FLOAT  
  --four         
""")

    def test_mixed(self):
        def fn(one, two='2', *more):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] one [more...]

Positional arguments:
  one      
  more...  

Options:
  --two=STR  
""")

    def test_require_excess(self):
        def fn(one, *more):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn one more...

Positional arguments:
  one      
  more...  
""",
            require_excess=True)

    def test_alias(self):
        def fn(one='1', two='2'):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] 

Options:
  -o, --one=STR  
  -t, --two=STR  
""",
            alias={'one': ('o',), 'two': ('t',)}
            )

    def test_force_positional(self):
        def fn(one='1', two='2'):
            pass
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] [one]

Positional arguments:
  one  

Options:
  --two=STR  
""",
            force_positional=('one',)
            )

    def test_doc(self):
        def fn(one, two='2', three=3, four=False, *more):
            """
            Command description

            one: First parameter

            two: Second parameter

            three: This help text spans
            over two lines in the source

            four: Fourth parameter

            more: Catch-all parameter

            Footnotes
            """
        self.assertHelpEquals(
            fn, """\
Usage: fn [OPTIONS] one [two] [more...]

Command description

Positional arguments:
  one       First parameter
  two       Second parameter(default: '2')
  more...   Catch-all parameter

Options:
  -t, --three=INT   This help text spans over two lines in the
                    source(default: 3)
  -f, --four        Fourth parameter

Footnotes
""",
            force_positional=('two',),
            alias={'three':('t',), 'four': ('f',)})

if __name__ == '__main__':
    unittest.main()
