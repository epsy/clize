# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import sys
import io
import inspect
import typing
import unittest
import warnings
from itertools import count
import contextlib

import attr
from docutils import frontend
import od
import repeated_test
from sigtools.support import f, s
from sigtools.modifiers import autokwoargs, kwoargs
from sigtools.wrappers import wrapper_decorator, decorator

from clize import runner, help, parser, util
from clize.tests.util import Fixtures, tup, any_instance_of

USAGE_HELP = 'func --help [--usage]'


def clize_helper_class(*args, **kwargs):
    return help.ClizeHelp(
        *args, builder=help.HelpForClizeDocstring.from_subject, **kwargs)


class WholeHelpTests(Fixtures):
    def _test(self, sig, doc, usage, help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func, helper_class=clize_helper_class)
        self._do_test(r, usage, help_str)

    def _do_test(self, runner, usage, help_str):
        h = runner.helper
        h.prepare()
        pc_usage = h.cli('func --help', '--usage')
        p_usage = [l.rstrip() for l in h.show_full_usage('func')]
        pc_help_str = h.cli('func --help')
        p_help_str = str(h.show('func'))
        self.assertEqual(usage, p_usage)
        self.assertEqual('\n'.join(usage), pc_usage)
        self.assertLinesEqual(help_str, p_help_str)
        self.assertLinesEqual(help_str, pc_help_str)


class ClizeWholeHelpTests(WholeHelpTests):
    def _test(self, *args, **kwargs):
        super(ClizeWholeHelpTests, self)._test(*args, **kwargs)

    simple = "one, *args, two", """
        Description

        one: Argument one

        args: Other arguments

        two: Option two

        Footer
    """, ['func --two=STR one [args...]', USAGE_HELP], """
        Usage: func [OPTIONS] one [args...]

        Description

        Arguments:
          one          Argument one
          args...      Other arguments

        Options:
          --two=STR    Option two

        Other actions:
          -h, --help   Show the help

        Footer
    """

    parens = "one:int, two=2, three=None, *args:int, alpha, beta:int, gamma=5", """
        Description

        one: Argument one

        two: Argument two

        three: Argument three

        args: Other arguments

        alpha: Option alpha

        beta: Option beta

        gamma: Option gamma

        Footer
    """, [
        'func --alpha=STR --beta=INT [--gamma=INT] '
             'one [two] [three] [args...]',
        USAGE_HELP
    ], """
        Usage: func [OPTIONS] one [two] [three] [args...]

        Description

        Arguments:
          one           Argument one (type: INT)
          two           Argument two (type: INT, default: 2)
          three         Argument three
          args...       Other arguments (type: INT)

        Options:
          --alpha=STR   Option alpha
          --beta=INT    Option beta
          --gamma=INT   Option gamma (default: 5)

        Other actions:
          -h, --help    Show the help

        Footer
    """

    pos_out_of_order = "one, two", """
        Description

        two: Argument two

        one: Argument one
    """, ['func one two', USAGE_HELP], """
        Usage: func one two

        Description

        Arguments:
          one          Argument one
          two          Argument two

        Other actions:
          -h, --help   Show the help
    """

    opt_out_of_order = "*, one, two", """
        two: Option two

        one: Option one
    """, ['func --two=STR --one=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Options:
          --two=STR    Option two
          --one=STR    Option one

        Other actions:
          -h, --help   Show the help
    """

    empty_docstring = "one, two, *, alpha, beta", "", [
        'func --alpha=STR --beta=STR one two', USAGE_HELP
        ], """
        Usage: func [OPTIONS] one two

        Arguments:
          one
          two

        Options:
          --alpha=STR
          --beta=STR

        Other actions:
          -h, --help    Show the help
    """

    short_name = '*, a', """
        a: alpha
    """, ['func -a STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Options:
          -a STR       alpha

        Other actions:
          -h, --help   Show the help
    """

    label = "*, alpha, beta", """
        desc

        alpha: Stuff

        Formatting options:

        beta: Other stuff
    """, ['func --alpha=STR --beta=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        desc

        Options:
          --alpha=STR   Stuff

        Formatting options:
          --beta=STR    Other stuff

        Other actions:
          -h, --help    Show the help
    """

    label_multi = "*, alpha, beta", """
        desc

        Formatting options:

        alpha: Stuff

        beta: Other stuff
    """, ['func --alpha=STR --beta=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        desc

        Formatting options:
          --alpha=STR   Stuff
          --beta=STR    Other stuff

        Other actions:
          -h, --help    Show the help
    """

    label_merge = "*, alpha, beta", """
        desc

        Formatting options:

        alpha: Stuff

        Formatting options:

        beta: Other stuff
    """, ['func --alpha=STR --beta=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        desc

        Formatting options:
          --alpha=STR   Stuff
          --beta=STR    Other stuff

        Other actions:
          -h, --help    Show the help
    """

    label_posarg = "one, two, *args, alpha", """
        Description

        one: Argument one

        Label:

        two: Argument two

        args: Other arguments

        alpha: Option alpha

        Footer
    """, ['func --alpha=STR one two [args...]', USAGE_HELP], """
        Usage: func [OPTIONS] one two [args...]

        Description

        Arguments:
          one           Argument one
          two           Argument two
          args...       Other arguments

        Label:
          --alpha=STR   Option alpha

        Other actions:
          -h, --help    Show the help

        Footer
    """

    undocumented = "one, two, *args:P.U, alpha, beta:P.U=1", """
        Description

        one: Argument one

        two: Argument two

        args: padding

        alpha: Option alpha

        beta: hidden opt

        Footer
    """, ['func --alpha=STR one two', USAGE_HELP], """
        Usage: func [OPTIONS] one two

        Description

        Arguments:
          one           Argument one
          two           Argument two

        Options:
          --alpha=STR   Option alpha

        Other actions:
          -h, --help    Show the help

        Footer
    """

    after_text = "one, two, *, alpha, beta", """
        Description

        one: Argument one

        after one

        two: Argument two

        after two

        alpha: Option alpha

        after alpha

        beta: Option beta

        after beta

        unknown: xxx

        Footer
    """, ['func --alpha=STR --beta=STR one two', USAGE_HELP], """
        Usage: func [OPTIONS] one two

        Description

        Arguments:
          one           Argument one

        after one

          two           Argument two

        after two

        Options:
          --alpha=STR   Option alpha

        after alpha

          --beta=STR    Option beta

        after beta

        Other actions:
          -h, --help    Show the help

        Footer
    """
    undocumented_all = "one:P.U, two:P.U, *args:P.U, alpha:P.U, beta:P.U", """
        Description

        two: unseen

        beta: unseen

        Footer
    """, ['func', USAGE_HELP], """
        Usage: func

        Description

        Other actions:
          -h, --help   Show the help

        Footer
    """


    num = "*, _6=False", """
        Description

        _6: Use IPv6?

        Footer
    """, ['func [-6]', USAGE_HELP], """
        Usage: func [OPTIONS]

        Description

        Options:
          -6           Use IPv6?

        Other actions:
          -h, --help   Show the help

        Footer
    """


    def test_nonclize_alt(self):
        @runner.Clize.as_is
        def alt(script):
            raise NotImplementedError
        def func():
            raise NotImplementedError
        r = runner.Clize(func, alt=alt)
        self._do_test(r, ['func', USAGE_HELP, 'func --alt [args...]'], """
            Usage: func

            Other actions:
              -h, --help   Show the help
              --alt
        """)


    def test_custom_param_help(self):
        class CustParam(parser.OptionParameter):
            def show_help(self, desc, after, f, cols):
                cols.append('I am', 'a custom parameter!')
                f.append("There is stuff after me.")
                f.append(desc)
                f.extend(after)
        func = f(
            "*, param: a",
            locals={'a': parser.use_class(named=CustParam, name="cust")})
        func.__doc__ = """
            param: Param desc

            After param

            _:_

        """
        r = runner.Clize(func)
        self._do_test(r, ['func --param=STR', USAGE_HELP], """
            Usage: func [OPTIONS]

            Options:
              I am         a custom parameter!

            There is stuff after me.

            Param desc

            After param

            Other actions:
              -h, --help   Show the help
        """)


class ClizeTokenizerTests(Fixtures):
    def _test(self, doc, tokens):
        self.assertEqual(
            list(help.elements_from_clize_docstring(inspect.cleandoc(doc))),
            tokens)

    none = '', []

    description = "This is just a description", [
        (help.EL_FREE_TEXT, "This is just a description", False)
    ]

    linewrap = """This is a description
    but it has to be on two lines""", [
        (help.EL_FREE_TEXT, "This is a description but it has to be on two lines", False)
    ]

    paragraphs = """This is a paragraph.

    This is also a paragraph.
    But this is just a line.""", [
        (help.EL_FREE_TEXT, "This is a paragraph.", False),
        (help.EL_FREE_TEXT, "This is also a paragraph. But this is just a line.", False),
    ]

    code = """This paragraph introduces code:

        This is code.
        It may not be line-wrapped.

        This is still code.
        No line wrapping.

    This is not code anymore.
    It may be line-wrapped.""", [
        (help.EL_FREE_TEXT, "This paragraph introduces code:", False),
        (help.EL_FREE_TEXT, "    This is code.\n    It may not be line-wrapped.", True),
        (help.EL_FREE_TEXT, "    This is still code.\n    No line wrapping.", True),
        (help.EL_FREE_TEXT, "This is not code anymore. It may be line-wrapped.", False),
    ]

    code_no_intro = """This is a paragraph.

    :

        This is code.""", [
        (help.EL_FREE_TEXT, "This is a paragraph.", False),
        (help.EL_FREE_TEXT, "    This is code.", True),
    ]

    parameter_doc = """
    param: This documents param.
    This still documents param.

    This doesn't.""", [
        (help.EL_PARAM_DESC, "param", "This documents param. This still documents param."),
        (help.EL_FREE_TEXT, "This doesn't.", False),
    ]

    parameter_after_text = """
    This is a description.

    p1: This documents p1.
    """, [
        (help.EL_FREE_TEXT, "This is a description.", False),
        (help.EL_PARAM_DESC, "p1", "This documents p1."),
    ]

    parameter_after_label = """
    Great parameters:

    p2: This documents p2.
    """, [
        (help.EL_LABEL, "Great parameters"),
        (help.EL_PARAM_DESC, "p2", "This documents p2."),
    ]

    labellike_before_paragraph = """
    This looks like a label:

    This is a paragraph.""", [
        (help.EL_FREE_TEXT, "This looks like a label:", False),
        (help.EL_FREE_TEXT, "This is a paragraph.", False),
    ]


class ClizeOrganizerTests(Fixtures):
    def _test(self, tokens, expected):
        self.assertEqual(
            list(help.helpstream_from_elements(tokens)),
            expected)

    def test_throws_on_unknown_token(self):
        with self.assertRaises(ValueError):
            self._test([
                (object(),)
            ], None)
        with self.assertRaises(ValueError):
            self._test([
                (help.HELP_HEADER,)
            ], None)

    empty = [], []

    free_text = [
        (help.EL_FREE_TEXT, "Free text 1", False),
        (help.EL_FREE_TEXT, "Free text 2", False),
    ], [
        (help.HELP_HEADER, "Free text 1", False),
        (help.HELP_HEADER, "Free text 2", False),
    ]

    parameter_descriptions = [
        (help.EL_PARAM_DESC, "param1", "description1"),
        (help.EL_PARAM_DESC, "param2", "description2"),
    ], [
        (help.HELP_PARAM_DESC, "param1", None, "description1"),
        (help.HELP_PARAM_DESC, "param2", None, "description2"),
    ]

    labels = [
        (help.EL_PARAM_DESC, "param1", "description1"),
        (help.EL_LABEL, "First label"),
        (help.EL_PARAM_DESC, "param2", "description2"),
        (help.EL_PARAM_DESC, "param3", "description3"),
        (help.EL_LABEL, "Second label"),
        (help.EL_PARAM_DESC, "param4", "description4"),
    ], [
        (help.HELP_PARAM_DESC, "param1", None, "description1"),
        (help.HELP_PARAM_DESC, "param2", "First label", "description2"),
        (help.HELP_PARAM_DESC, "param3", "First label", "description3"),
        (help.HELP_PARAM_DESC, "param4", "Second label", "description4"),
    ]

    footnotes = [
        (help.EL_PARAM_DESC, "param1", "description1"),
        (help.EL_FREE_TEXT, "This is the footnotes.", False),
        (help.EL_FREE_TEXT, "This is preformatted.", True),
    ], [
        (help.HELP_PARAM_DESC, "param1", None, "description1"),
        (help.HELP_FOOTER, "This is the footnotes.", False),
        (help.HELP_FOOTER, "This is preformatted.", True),
    ]

    header_and_footnotes = [
        (help.EL_FREE_TEXT, "This is a description.", False),
        (help.EL_FREE_TEXT, "This is preformatted.", True),
        (help.EL_PARAM_DESC, "param1", "description"),
        (help.EL_FREE_TEXT, "This is the footnotes.", False),
        (help.EL_FREE_TEXT, "This is also preformatted.", True),
    ], [
        (help.HELP_HEADER, "This is a description.", False),
        (help.HELP_HEADER, "This is preformatted.", True),
        (help.HELP_PARAM_DESC, "param1", None, "description"),
        (help.HELP_FOOTER, "This is the footnotes.", False),
        (help.HELP_FOOTER, "This is also preformatted.", True),
    ]

    param_after = [
        (help.EL_PARAM_DESC, "param1", "description"),
        (help.EL_FREE_TEXT, "Additional description for param1", False),
        (help.EL_FREE_TEXT, "Additional preformatted text for param1", True),
        (help.EL_PARAM_DESC, "param2", "another description"),
    ], [
        (help.HELP_PARAM_DESC, "param1", None, "description"),
        (help.HELP_PARAM_AFTER, "param1", "Additional description for param1", False),
        (help.HELP_PARAM_AFTER, "param1", "Additional preformatted text for param1", True),
        (help.HELP_PARAM_DESC, "param2", None, "another description"),
    ]

    explicit_after = [
        (help.EL_PARAM_DESC, "param1", "param1 description"),
        (help.EL_AFTER, "param1", "after param 1", False),
        (help.EL_FREE_TEXT, "still after param 1", False),
        (help.EL_PARAM_DESC, "param2", "param2 description"),
        (help.EL_AFTER, "param2", "after param 2", False),
        (help.EL_FREE_TEXT, "footnotes", False),
    ], [
        (help.HELP_PARAM_DESC, "param1", None, "param1 description"),
        (help.HELP_PARAM_AFTER, "param1", "after param 1", False),
        (help.HELP_PARAM_AFTER, "param1", "still after param 1", False),
        (help.HELP_PARAM_DESC, "param2", None, "param2 description"),
        (help.HELP_PARAM_AFTER, "param2", "after param 2", False),
        (help.HELP_FOOTER, "footnotes", False)
    ]


class HelpForParametersBlankFromSignature(Fixtures):
    def _test(self, parameters, sections):
        self._do_test(
            parser.CliSignature(parameters),
            help.HelpForParameters([], [], sections, {}))

    def _do_test(self, signature, expected):
        ch = help.HelpForParameters.blank_from_signature(signature)
        self.assertEqual(attr.asdict(ch), attr.asdict(expected))

    empty = [], od[
        help.LABEL_POS: od(),
        help.LABEL_OPT: od(),
        help.LABEL_ALT: od(),
    ]

    _param_pos = parser.PositionalParameter(
        argument_name='pos', display_name='pos')
    _param_opt = parser.OptionParameter(
        argument_name='opt', aliases=['--opt'])
    _param_alt = parser.AlternateCommandParameter(
        aliases=['--alt'], func=None)

    _param_pos_z = parser.PositionalParameter(
        argument_name='zpos', display_name='zpos')
    _param_opt_z = parser.OptionParameter(
        argument_name='zopt', aliases=['--zopt'])
    _param_alt_z = parser.AlternateCommandParameter(
        aliases=['--zalt'], func=None)

    params = [
        _param_pos,
        _param_opt,
        _param_alt,
    ], od[
        help.LABEL_POS: od[
            'pos': (_param_pos, ''),
        ],
        help.LABEL_OPT: od[
            'opt': (_param_opt, ''),
        ],
        help.LABEL_ALT: od[
            '--alt': (_param_alt, ''),
        ],
    ]

    params_sort = [
        _param_pos_z, _param_pos, # positional parameters keep source order
        _param_opt_z, _param_opt,
        _param_alt_z, _param_alt,
    ], od[
        help.LABEL_POS: od[
            'zpos': (_param_pos_z, ''),
            'pos': (_param_pos, ''),
        ],
        help.LABEL_OPT: od[
            'opt': (_param_opt, ''),
            'zopt': (_param_opt_z, ''),
        ],
        help.LABEL_ALT: od[
            '--zalt': (_param_alt_z, ''),
            '--alt': (_param_alt, ''),
        ],
    ]

    _param_pos_u = parser.PositionalParameter(
        argument_name='upos', display_name='upos',
        undocumented=True)
    _param_opt_u = parser.OptionParameter(
        argument_name='uopt', aliases=['--uopt'],
        undocumented=True)
    _param_alt_u = parser.AlternateCommandParameter(
        aliases=['--ualt'], func=None,
        undocumented=True)

    undocumented = [
        _param_pos, _param_pos_u,
        _param_opt, _param_opt_u,
        _param_alt, _param_alt_u,
    ], od[
        help.LABEL_POS: od[
            'pos': (_param_pos, ''),
        ],
        help.LABEL_OPT: od[
            'opt': (_param_opt, ''),
        ],
        help.LABEL_ALT: od[
            '--alt': (_param_alt, ''),
        ],
    ]


hfcd = help.HelpForClizeDocstring
ANY_CLIZE_PARAM = any_instance_of(parser.Parameter)


class HelpForClizeDocstringAddHelpstream(Fixtures):
    def _test(self, signature, stream, pnames, primary, exp_help_state):
        csig = parser.CliSignature.from_signature(s(signature))
        self._do_test(hfcd.blank_from_signature(csig),
                      stream, pnames, primary, exp_help_state)

    def _do_test(self, help_state, stream, pnames, primary, exp_help_state):
        help_state.add_helpstream(stream, pnames, primary)
        self.assertEqual(attr.asdict(exp_help_state), attr.asdict(help_state))

    empty = '', [], None, False, hfcd([], [], od[
        help.LABEL_POS: od(),
        help.LABEL_OPT: od(),
        help.LABEL_ALT: od(),
    ], {})

    ignore_missing_param = '', [
        (help.HELP_PARAM_DESC, "opt", None, "option"),
    ], None, True, hfcd([], [], od[
        help.LABEL_POS: od(),
        help.LABEL_OPT: od(),
        help.LABEL_ALT: od(),
    ], {})

    full = 'pos, *, opt', [
        (help.HELP_HEADER, "Description.", False),
        (help.HELP_HEADER, "More description.", False),
        (help.HELP_HEADER, "Some code.", True),
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_AFTER, "pos", "after positional", False),
        (help.HELP_PARAM_DESC, "opt", None, "option"),
        (help.HELP_PARAM_AFTER, "opt", "after option", False),
        (help.HELP_FOOTER, "A footer.", False),
    ], None, True, hfcd([
        "Description.", "More description.", "Some code.",
    ], [
        "A footer.",
    ], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt": (ANY_CLIZE_PARAM, "option"),
        ],
        help.LABEL_ALT: od(),
    ], {
        "pos": ["after positional"],
        "opt": ["after option"],
    })

    ignore_nonprimary_header_and_footer = "pos, *, opt", [
        (help.HELP_HEADER, "Description.", False),
        (help.HELP_HEADER, "More description.", False),
        (help.HELP_HEADER, "Some code.", True),
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_AFTER, "pos", "after positional", False),
        (help.HELP_PARAM_DESC, "opt", None, "option"),
        (help.HELP_PARAM_AFTER, "opt", "after option", False),
        (help.HELP_FOOTER, "A footer.", False),
    ], None, False, hfcd([], [], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt": (ANY_CLIZE_PARAM, "option"),
        ],
        help.LABEL_ALT: od(),
    ], {
        "pos": ["after positional"],
        "opt": ["after option"],
    })

    pnames = "pos, *, opt", [
        (help.HELP_HEADER, "Description.", False),
        (help.HELP_HEADER, "More description.", False),
        (help.HELP_HEADER, "Some code.", True),
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_AFTER, "pos", "after positional", False),
        (help.HELP_PARAM_DESC, "opt", None, "option"),
        (help.HELP_PARAM_AFTER, "opt", "after option", False),
        (help.HELP_FOOTER, "A footer.", False),
    ], ['pos'], False, hfcd([], [], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt": (ANY_CLIZE_PARAM, ""),
        ],
        help.LABEL_ALT: od(),
    ], {
        "pos": ["after positional"],
    })

    label = 'pos, *, opt1, opt2, opt3', [
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_DESC, "opt1", None, "option 1"),
        (help.HELP_PARAM_DESC, "opt2", "Label", "option 2"),
        (help.HELP_PARAM_DESC, "opt3", "Label", "option 3"),
    ], None, True, hfcd([], [], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt1": (ANY_CLIZE_PARAM, "option 1"),
        ],
        "Label": od[
            "opt2": (ANY_CLIZE_PARAM, "option 2"),
            "opt3": (ANY_CLIZE_PARAM, "option 3"),
        ],
        help.LABEL_ALT: od(),
    ], {})

    order = 'pos, *, opt1, opt2, opt3', [
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_DESC, "opt1", None, "option 1"),
        (help.HELP_PARAM_DESC, "opt3", None, "option 3"),
        (help.HELP_PARAM_DESC, "opt2", None, "option 2"),
    ], None, True, hfcd([], [], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt1": (ANY_CLIZE_PARAM, "option 1"),
            "opt3": (ANY_CLIZE_PARAM, "option 3"),
            "opt2": (ANY_CLIZE_PARAM, "option 2"),
        ],
        help.LABEL_ALT: od(),
    ], {})

    label_order = 'pos, *, opt1, opt2, opt3', [
        (help.HELP_PARAM_DESC, "pos", None, "positional"),
        (help.HELP_PARAM_DESC, "opt1", None, "option 1"),
        (help.HELP_PARAM_DESC, "opt3", "First label", "option 3"),
        (help.HELP_PARAM_DESC, "opt2", "Second label", "option 2"),
    ], None, True, hfcd([], [], od[
        help.LABEL_POS: od[
            "pos": (ANY_CLIZE_PARAM, "positional"),
        ],
        help.LABEL_OPT: od[
            "opt1": (ANY_CLIZE_PARAM, "option 1"),
        ],
        "First label": od[
            "opt3": (ANY_CLIZE_PARAM, "option 3"),
        ],
        "Second label": od[
            "opt2": (ANY_CLIZE_PARAM, "option 2"),
        ],
        help.LABEL_ALT: od(),
    ], {})

    def test_invalid_help_type(self):
        with self.assertRaises(ValueError):
            self._test("", [
                (object(),),
            ], None, True, None)


class SphinxTokenizerTests(Fixtures):
    def _test(self, docstring, exp_tokens):
        self.assertEqual(
            exp_tokens,
            list(help.elements_from_sphinx_docstring(
                inspect.cleandoc(docstring), 'func'))
            )

    paragraphs = """
        This is a paragraph.

        This paragraph
        spans over
        multiple lines.

        Linebreaks after periods.
        They carry two spaces.

        But it doesn't break Mr. or Ms. Lastname's inline spacing.
    """, [
        (help.EL_FREE_TEXT, "This is a paragraph.", False),
        (help.EL_FREE_TEXT, "This paragraph spans over multiple lines.", False),
        (help.EL_FREE_TEXT, "Linebreaks after periods.  They carry two spaces.", False),
        (help.EL_FREE_TEXT, "But it doesn't break Mr. or Ms. Lastname's inline spacing.", False),
    ]

    trailing_spaces = """
        There are trailing spaces here.   \n\
        They should be ignored.
    """, [
        (help.EL_FREE_TEXT, "There are trailing spaces here.  They should be ignored.", False),
    ]

    after = """
        Description

        :param opt1:
            option 1 description.
            Still option 1 description.

            After option 1

        Also after option 1

        :param opt2: option 2 description.

            After option 2

        Footnotes
    """, [
        (help.EL_FREE_TEXT, "Description", False),
        (help.EL_PARAM_DESC, "opt1", "option 1 description.  Still option 1 description."),
        (help.EL_AFTER, "opt1", "After option 1", False),
        (help.EL_FREE_TEXT, "Also after option 1", False),
        (help.EL_PARAM_DESC, "opt2", "option 2 description."),
        (help.EL_AFTER, "opt2", "After option 2", False),
        (help.EL_FREE_TEXT, "Footnotes", False),
    ]

    fields = """
        :noindex:

        Description

        :param str opt1: option 1 description
        :param opt2: option 2 description
        :type opt2: str
        :return: a return value
        :rtype: return value type
        :raises ValueError: if there is an error in the value
        :raises OtherEeror: Subnodes should be ignored in field bodies

            ::

                This is code.

        Footnotes
    """, [
        (help.EL_FREE_TEXT, "Description", False),
        (help.EL_PARAM_DESC, "opt1", "option 1 description"),
        (help.EL_PARAM_DESC, "opt2", "option 2 description"),
        (help.EL_FREE_TEXT, "Footnotes", False),
    ]

    markup = """
        `docutils <https://pypi.python.org/pypi/docutils>`_ offers a *range*
        of `different` markup ``options.``
        Clize should **not** render most of them.

        :param opt: This also applies *inside* parameters.
    """, [
        (help.EL_FREE_TEXT, "docutils offers a range of different markup "
                             "options.  Clize should not render most of them.",
         False),
        (help.EL_PARAM_DESC, "opt", "This also applies inside parameters."),
    ]

    literal_block = """
        Code can be denoted at the end of paragraphs::

            This is
            code.

            This is still
            code.

        You can also begin them without a paragraph

        ::

            This is
            also code.

        :param opt1: They are also available in field bodies

            ::

                This is
                code.

        :param opt2:

            ::

                This is
                also code.
    """, [
        (help.EL_FREE_TEXT, "Code can be denoted at the end of paragraphs:", False),
        (help.EL_FREE_TEXT, "    This is\n    code.\n    \n    This is still\n    code.", True),
        (help.EL_FREE_TEXT, "You can also begin them without a paragraph", False),
        (help.EL_FREE_TEXT, "    This is\n    also code.", True),
        (help.EL_PARAM_DESC, "opt1", "They are also available in field bodies"),
        (help.EL_AFTER, "opt1", "    This is\n    code.", True),
        (help.EL_PARAM_DESC, "opt2", ""),
        (help.EL_AFTER, "opt2", "    This is\n    also code.", True),
    ]

    code = """
        .. code::

            This is
            code.

        .. code:: python

            def some_python(code):
                pass

        :param opt1: also in parameters

            .. code::

                This is
                code.
    """, [
        (help.EL_FREE_TEXT, "    This is\n    code.", True),
        (help.EL_FREE_TEXT, "    def some_python(code):\n        pass", True),
        (help.EL_PARAM_DESC, "opt1", "also in parameters"),
        (help.EL_AFTER, "opt1", "    This is\n    code.", True),
    ]

    labels = """
        Description

        :param opt1: option 1

        This is a label:

        :param opt2: option 2
        :param opt3: option 3

        Another label:

        :param opt4: option 4
    """, [
        (help.EL_FREE_TEXT, "Description", False),
        (help.EL_PARAM_DESC, "opt1", "option 1"),
        (help.EL_LABEL, "This is a label"),
        (help.EL_PARAM_DESC, "opt2", "option 2"),
        (help.EL_PARAM_DESC, "opt3", "option 3"),
        (help.EL_LABEL, "Another label"),
        (help.EL_PARAM_DESC, "opt4", "option 4"),
    ]

    substitution = """
        Hello I am |name|.

        .. |name| replace:: a computer program
    """, [
        (help.EL_FREE_TEXT, "Hello I am a computer program.", False),
    ]


def sphinx_helper_class(*args, **kwargs):
    return help.ClizeHelp(
        *args, builder=help.HelpForSphinxDocstring.from_subject, **kwargs)


hfsd = help.HelpForSphinxDocstring


class SphinxAddDocstringTests(Fixtures):
    def _test(self, signature, docstring, pnames, primary, exp_help_state):
        csig = parser.CliSignature.from_signature(s(signature))
        self._do_test(hfsd.blank_from_signature(csig),
                      docstring, pnames, primary, exp_help_state)

    def _do_test(self, help_state, docstring, pnames, primary, exp_help_state):
        help_state.add_docstring(docstring, 'func', pnames, primary)
        self.assertEqual(attr.asdict(exp_help_state), attr.asdict(help_state))

    description_and_args = "arg1, arg2, *, opt1, opt2", """
        Description

        :param arg1: This is arg1
        :param arg2: This is arg2
        :param opt1: This is opt1
        :param opt2: This is opt2

        Footnotes
    """, None, True, hfsd([
        "Description",
    ], [
        "Footnotes",
    ], od[
        help.LABEL_POS: od[
            "arg1": (ANY_CLIZE_PARAM, "This is arg1"),
            "arg2": (ANY_CLIZE_PARAM, "This is arg2"),
        ],
        help.LABEL_OPT: od[
            "opt1": (ANY_CLIZE_PARAM, "This is opt1"),
            "opt2": (ANY_CLIZE_PARAM, "This is opt2"),
        ],
        help.LABEL_ALT: od(),
    ], {})

    after = "*, opt1, opt2", """
        Description

        :param opt1:
            option 1 description.
            Still option 1 description.

            After option 1

        Also after option 1

        :param opt2: option 2 description.

            After option 2

        Footnotes
    """, None, True, hfsd([
        "Description",
    ], [
        "Footnotes",
    ], od[
        help.LABEL_POS: od(),
        help.LABEL_OPT: od[
            "opt1": (ANY_CLIZE_PARAM, "option 1 description.  Still option 1 description."),
            "opt2": (ANY_CLIZE_PARAM, "option 2 description."),
        ],
        help.LABEL_ALT: od(),
    ], {
        "opt1": ["After option 1", "Also after option 1"],
        "opt2": ["After option 2"],
    })


class SphinxWholeHelpTests(WholeHelpTests):
    def _test(self, sig, doc, usage, help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func, helper_class=sphinx_helper_class)
        self._do_test(r, usage, help_str)

    description_and_args = "arg1, arg2, *, opt1, opt2", """
        Description

        :param arg1: This is arg1
        :param arg2: This is arg2
        :param opt1: This is opt1
        :param opt2: This is opt2

        Footnotes
    """, ['func --opt1=STR --opt2=STR arg1 arg2', USAGE_HELP], """
        Usage: func [OPTIONS] arg1 arg2

        Description

        Arguments:
          arg1         This is arg1
          arg2         This is arg2

        Options:
          --opt1=STR   This is opt1
          --opt2=STR   This is opt2

        Other actions:
          -h, --help   Show the help

        Footnotes
    """

    after = "*, opt1, opt2", """
        Description

        :param opt1: This is opt1.
            Still in the first paragraph for opt1.

            New paragraph for opt1

        :param opt2: This is opt2

        Footnotes
    """, ['func --opt1=STR --opt2=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Description

        Options:
          --opt1=STR   This is opt1.  Still in the first paragraph for opt1.

        New paragraph for opt1

          --opt2=STR   This is opt2

        Other actions:
          -h, --help   Show the help

        Footnotes
    """

    literal_block = "*, opt1, opt2", """
        Code can be denoted at the end of paragraphs::

            This is
            code.

            This is still
            code.

        You can also begin them without a paragraph

        ::

            This is
            also code.

        :param opt1: They are also available in field bodies

            ::

                This is
                code.

        :param opt2:

            ::

                This is
                also code.
    """, ['func --opt1=STR --opt2=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Code can be denoted at the end of paragraphs:

            This is
            code.

            This is still
            code.

        You can also begin them without a paragraph

            This is
            also code.

        Options:
          --opt1=STR   They are also available in field bodies

            This is
            code.

          --opt2=STR

            This is
            also code.

        Other actions:
          -h, --help   Show the help
    """


class AutodetectHelpFormatTests(WholeHelpTests):
    def _test(self, sig, doc, exp_help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func)
        h = r.helper
        pc_help_str = h.cli('func --help')
        p_help_str = str(h.show('func'))
        self.assertLinesEqual(exp_help_str, p_help_str)
        self.assertLinesEqual(exp_help_str, pc_help_str)

    sphinx_desc_params = "arg1, arg2, *, opt1, opt2", """
        Description

        :param arg1: This is arg1
        :param arg2: This is arg2
        :param opt1: This is opt1
        :param opt2: This is opt2

        Footnotes
    """, """
        Usage: func [OPTIONS] arg1 arg2

        Description

        Arguments:
          arg1         This is arg1
          arg2         This is arg2

        Options:
          --opt1=STR   This is opt1
          --opt2=STR   This is opt2

        Other actions:
          -h, --help   Show the help

        Footnotes
    """

    clize_desc_params = "one, *args, two", """
        Description

        one: Argument one

        args: Other arguments

        two: Option two

        Footer
    """, """
        Usage: func [OPTIONS] one [args...]

        Description

        Arguments:
          one          Argument one
          args...      Other arguments

        Options:
          --two=STR    Option two

        Other actions:
          -h, --help   Show the help

        Footer
    """


@contextlib.contextmanager
def capture_stderr():
    orig_stderr = sys.stderr
    stderr = io.StringIO()
    try:
        sys.stderr = stderr
        yield stderr
    finally:
        sys.stderr = orig_stderr


@attr.define
class DocutilsVersion:
    name: str
    docutils_frontend: typing.Any
    warn_filters: typing.Sequence[typing.Any] = ()

    def __repr__(self):
        return f'<{self.name}>'


class OmitAttributes:
    def __init__(self, instance, omit):
        self.__instance = instance
        self.__omit = omit

    def __getattr__(self, item):
        if item in self.__omit:
            raise AttributeError(item)
        return getattr(self.__instance, item)


real_docutils = DocutilsVersion("real_docutils", frontend)
pre_19_docutils = DocutilsVersion(
    "pre_19_docutils",
    OmitAttributes(frontend, {"get_default_settings"}),
    [
        {"action": "ignore", "message": r".*Option.*\b0\.21\b.*", "category": DeprecationWarning},
    ],
)


@repeated_test.with_options_matrix(
    docutils_frontend_module=[
        real_docutils,
        pre_19_docutils,
    ]
)
class ElementsFromAutodetectedDocstringTests(Fixtures):
    def _test(self, docstring, exp_helpstream, *, exp_stderr='', docutils_frontend_module: DocutilsVersion):
        with capture_stderr() as stderr, warnings.catch_warnings():
            for warn_filter in docutils_frontend_module.warn_filters:
                warnings.filterwarnings(**warn_filter)
            helpstream = list(help.elements_from_autodetected_docstring(
                docstring, 'func',
                _docutils_frontend_module=docutils_frontend_module.docutils_frontend
            ))
        self.assertEqual(exp_helpstream, helpstream)
        self.assertLinesEqual(exp_stderr, stderr.getvalue())

    none = None, []
    empty = "", []

    clize_sphinx_error = """
        this is an :unknown:`ref`
    """, [
        (help.EL_FREE_TEXT, 'this is an :unknown:`ref`', False),
    ]

    clize_has_sphinx_error = """
        Description

        param: deals with backquotes `like that one
    """, [
        (help.EL_FREE_TEXT, 'Description', False),
        (help.EL_PARAM_DESC, 'param', 'deals with backquotes `like that one'),
    ]

    sphinx_has_sphinx_error_in_free_text = """
        Description

        :param param: param desc

        backquotes `like that one don't generate text in the help
    """, [
        (help.EL_FREE_TEXT, 'Description', False),
        (help.EL_PARAM_DESC, 'param', 'param desc'),
        (help.EL_FREE_TEXT, 'backquotes `like that one don\'t generate text in the help', False),
    ], repeated_test.options(
        exp_stderr=
            "func:6: (WARNING/2) Inline interpreted text or phrase reference "
            "start-string without end-string."
    )

    sphinx_has_sphinx_error_in_param_desc = """
        Description

        :param param: deals with backquotes `like that one
    """, [
        (help.EL_FREE_TEXT, 'Description', False),
        (help.EL_PARAM_DESC, 'param', 'deals with backquotes `like that one'),
    ], repeated_test.options(
        exp_stderr=
            "func:4: (WARNING/2) Inline interpreted text or phrase reference "
            "start-string without end-string."
    )


class WrappedFuncTests(Fixtures):
    def _test(self, sig, wrapper_sigs, doc, wrapper_docs, help_str):
        ifunc = f(sig, pre="from clize import Parameter")
        ifunc.__doc__ = doc
        func = ifunc
        for sig, doc in zip(wrapper_sigs, wrapper_docs):
            wfunc = f('func, ' + sig, pre="from clize import Parameter")
            wfunc.__doc__ = doc
            func = wrapper_decorator(wfunc)(func)
        r = runner.Clize(func)
        h = help.ClizeHelp(r, None)
        h.prepare()
        p_help_str = str(h.show('func'))
        self.assertLinesEqual(help_str, p_help_str)

    args = 'one, *, alpha', [
        'three, *args, gamma, **kwargs',
        'two, *args, beta, **kwargs',
    ], "", ["", ""], """
        Usage: func [OPTIONS] two three one

        Arguments:
          two
          three
          one

        Options:
          --alpha=STR
          --beta=STR
          --gamma=STR

        Other actions:
          -h, --help    Show the help
    """

    docs = 'one, *, alpha', [
        'three, *args, gamma, **kwargs',
        'two, *args, beta, **kwargs',
    ], """
        one: One

        alpha: Alpha
    """, ["""
        three: Three

        gamma: Gamma
    """, """
        two: Two

        beta: Beta
    """], """
        Usage: func [OPTIONS] two three one

        Arguments:
          two           Two
          three         Three
          one           One

        Options:
          --alpha=STR   Alpha
          --beta=STR    Beta
          --gamma=STR   Gamma

        Other actions:
          -h, --help    Show the help
    """

    separate_labels = 'one, *, alpha', [
        'three, *args, gamma, **kwargs',
        'two, *args, beta, **kwargs',
    ], """
        one: One

        alpha: Alpha
    """, ["""
        three: Three

        Label gamma:

        gamma: Gamma
    """, """
        two: Two

        Label beta:

        beta: Beta
    """], """
        Usage: func [OPTIONS] two three one

        Arguments:
          two           Two
          three         Three
          one           One

        Options:
          --alpha=STR   Alpha

        Label beta:
          --beta=STR    Beta

        Label gamma:
          --gamma=STR   Gamma

        Other actions:
          -h, --help    Show the help
    """

    merged_labels = 'one, *, alpha', [
        'three, *args, gamma, **kwargs',
        'two, *args, beta, **kwargs',
    ], """
        one: One

        alpha: Alpha
    """, ["""
        three: Three

        Label:

        gamma: Gamma
    """, """
        two: Two

        Label:

        beta: Beta
    """], """
        Usage: func [OPTIONS] two three one

        Arguments:
          two           Two
          three         Three
          one           One

        Options:
          --alpha=STR   Alpha

        Label:
          --beta=STR    Beta
          --gamma=STR   Gamma

        Other actions:
          -h, --help    Show the help
    """


def _other_func(spam, ham, eggs):
    """
    spam: param spam

    ham: param ham

    eggs: param eggs

    alpha: param alpha can't be taken over
    """
    pass


@kwoargs('delegated_to')
def _order_del(delegated_to):
    """:param delegated_to: delegated_to param"""


class AutoforwardedFuncTests(Fixtures):
    def _test(self, func, help_str):
        r = runner.Clize(func)
        h = help.ClizeHelp(r, None)
        h.prepare()
        p_help_str = str(h.show('func'))
        self.assertLinesEqual(help_str, p_help_str)

    def _decorator_three(func):
        @autokwoargs
        def _wrapper(one, two, three=3, *args, **kwargs):
            """
            one: param one

            two: param two

            three: param three
            """
            func(*args, **kwargs)
        _wrapper.__name__ = func.__name__
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two alpha beta
        Description

        Arguments:
          one           param one
          two           param two
          alpha         param alpha
          beta          param beta

        Options:
          --gamma=STR   param gamma
          --three=INT   param three (default: 3)

        Other actions:
          -h, --help    Show the help
    """)
    @_decorator_three
    @autokwoargs
    def decorated(alpha, beta, gamma=None):
        """
        Description

        alpha: param alpha

        beta: param beta

        gamma: param gamma
        """
        return alpha, beta, gamma

    def _decorator_four(func):
        @autokwoargs
        def _wrapper(one, two, three=3, four=4, *args, **kwargs):
            """
            one: param one

            two: param two

            three: param three

            beta: this shouldn't even be here

            Label:

            gamma: this either

            four: param four
            """
            func(42, *args, **kwargs)
        _wrapper.__name__ = func.__name__
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two beta
        description in func

        Arguments:
          one           param one in subject
          two           param two
          beta

        Options:
          --gamma=STR   param gamma
          --three=INT   param three (default: 3)

        Label:
          --four=INT    param four (default: 4)

        Other actions:
          -h, --help    Show the help
    """)
    @_decorator_four
    @autokwoargs
    def messy_docstrings(one, beta, gamma=None):
        """
        description in func

        one: param one in subject

        gamma: param gamma
        """
        return one, beta, gamma

    def _decorator_1(func):
        @autokwoargs
        def _wrapper(one, two, three=3, *args, **kwargs):
            """
            description in decorator A

            one: param one

            free in decorator A after one

            two: param two

            free in decorator A after two

            three: param three

            free in decorator A after three

            beta: this shouldn't even be in decorator A

            free in decorator A after beta

            gamma: this either

            footnotes in decorator A
            """
            func(*args, **kwargs)
        _wrapper.__name__ = func.__name__
        return _wrapper


    def _decorator_2(func):
        @autokwoargs
        def _wrapper(four, five, six=6, *args, **kwargs):
            """
            description in decorator B

            four: param four

            free in decorator B after four

            five: param five

            free in decorator B after five

            six: param six

            free in decorator B after six

            beta: this shouldn't even be in decorator B

            free in decorator B after beta

            gamma: this either

            footnotes in decorator B
            """
            func(*args, **kwargs)
        _wrapper.__name__ = func.__name__
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two four five alpha beta

        description in func

        Arguments:
          one           param one
        free in decorator A after one
          two           param two
        free in decorator A after two
          four          param four
        free in decorator B after four
          five          param five
        free in decorator B after five
          alpha         param alpha
        free in func after alpha
          beta          param beta
        free in func after beta

        Options:
          --gamma=STR   param gamma
        free in func after gamma
          --three=INT   param three (default: 3)
        free in decorator A after three
          --six=INT     param six (default: 6)
        free in decorator B after six

        Other actions:
          -h, --help    Show the help

        footnotes in func
    """)
    @_decorator_1
    @_decorator_2
    @autokwoargs
    def double_decorators(alpha, beta, gamma=None):
        """
        description in func

        alpha: param alpha

        free in func after alpha

        beta: param beta

        free in func after beta

        gamma: param gamma

        free in func after gamma

        _:_

        footnotes in func
        """
        return alpha, beta, gamma

    @tup("""
        Usage: func [OPTIONS] one two beta

        Arguments:
          one           param one
          two           param two
          beta          param beta

        Options:
          --three=INT   param three takeover (default: 3)

        Label:
          --four=INT    param four (default: 4)

        Other actions:
          -h, --help    Show the help
    """)
    @_decorator_four
    def doc_takeover(alpha, beta):
        """
        beta: param beta

        three: param three takeover
        """
        return alpha

    @tup("""
        Usage: func alpha beta spam ham eggs

        Arguments:
          alpha        param alpha
          beta         param beta
          spam         param spam
          ham          param ham
          eggs         param eggs takeover

        Other actions:
          -h, --help   Show the help
    """)
    def main_forwards_to_other(alpha, beta, *args, **kwargs):
        """
        alpha: param alpha

        beta: param beta

        eggs: param eggs takeover
        """
        _other_func(*args, **kwargs)


    @tup("""
        Usage: func [OPTIONS] one two

        Description from func

        Arguments:
          one           param one
        free in decorator A after one
          two           param two
        free in decorator A after two

        Options:
          --three=INT   param three (default: 3)
        free in decorator A after three

        Other actions:
          -h, --help    Show the help
    """)
    @_decorator_1
    def deepest_has_no_params():
        """Description from func"""
        return


    @decorator
    @kwoargs('one')
    def _order_1(func, one, *args, **kwargs):
        """:param one: one param"""
        return func(*args, **kwargs)

    @decorator
    @kwoargs('two', 'override')
    def _order_2(func, two, override, *args, **kwargs):
        """
        :param two: two param
        :param override: override param
        """
        return func(*args, **kwargs)

    @tup("""
        Usage: func [OPTIONS]

        Options:
          --main=STR           main param
          --override=STR       overridden in main
          --one=STR            one param
          --two=STR            two param
          --delegated-to=STR   delegated_to param

        Other actions:
          -h, --help           Show the help
    """)
    @_order_1
    @_order_2
    @kwoargs('main')
    def sources_order(main, *args, **kwargs):
        """
        :param main: main param
        :param override: overridden in main
        """
        return _order_del(*args, **kwargs)


class FormattingTests(Fixtures):
    def _test(self, sig, doc, help_str):
        try:
            backw = util.get_terminal_width
        except AttributeError:
            backw = None
        try:
            util.get_terminal_width = lambda: 80
            func = f(sig, pre="from clize import Parameter as P")
            func.__doc__ = doc
            r = runner.Clize(func)
            h = help.ClizeHelp(r, None)
            h.prepare()
            p_help_str = str(h.show('func'))
            self.assertEqual(help_str, p_help_str)
        finally:
            if backw is not None:
                util.get_terminal_width = backw

    wrap = "", """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis a est neque. Nullam ornare sem eu commodo gravida.
        """, (
            "Usage: func\n"
            "\n"
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                                                    "Duis a est neque.\n"
            "Nullam ornare sem eu commodo gravida.\n"
            "\n"
            "Other actions:\n"
            "  -h, --help   Show the help"
        )
    code_block = "*, alpha, beta", """
            This is a code example:

                Code  is     not
                auto-formatted

                It    really  isn't

            Here ends the code example.
        """, (
            "Usage: func [OPTIONS]\n"
            "\n"
            "This is a code example:\n"
            "\n"
            "    Code  is     not\n"
            "    auto-formatted\n"
            "\n"
            "    It    really  isn't\n"
            "\n"
            "Here ends the code example.\n"
            "\n"
            "Options:\n"
            "  --alpha=STR\n"
            "  --beta=STR\n"
            "\n"
            "Other actions:\n"
            "  -h, --help    Show the help"
        )

    code_block_nocolon = "*, alpha, beta", """
            Following is a code example.

            :

                Code  is     not
                auto-formatted

                It    really  isn't

            Here ends the code example.
        """, (
            "Usage: func [OPTIONS]\n"
            "\n"
            "Following is a code example.\n"
            "\n"
            "    Code  is     not\n"
            "    auto-formatted\n"
            "\n"
            "    It    really  isn't\n"
            "\n"
            "Here ends the code example.\n"
            "\n"
            "Options:\n"
            "  --alpha=STR\n"
            "  --beta=STR\n"
            "\n"
            "Other actions:\n"
            "  -h, --help    Show the help"
        )

    unindented_not_a_code_block = "*, alpha, beta", """
        This is not a code block:

        This   is  not  a
        code block.
    """, (
        "Usage: func [OPTIONS]\n"
        "\n"
        "This is not a code block:\n"
        "\n"
        "This is not a code block.\n"
        "\n"
        "Options:\n"
        "  --alpha=STR\n"
        "  --beta=STR\n"
        "\n"
        "Other actions:\n"
        "  -h, --help    Show the help"
    )


class DispatcherHelper(Fixtures):
    def _test(self, description, footer, sigs, docs, usage, help_str):
        funcs = []
        for i, sig, doc in zip(count(1), sigs, docs):
            func = f(sig)
            func.__doc__ = doc
            func.__name__ = 'func' + str(i)
            funcs.append(func)
        sd = runner.SubcommandDispatcher(funcs, description, footer)
        self._do_test(sd, usage, help_str)

    def _do_test(self, sd, usage, help_str):
        h = sd.cli.helper
        h.prepare()
        p_usage = list(h.show_full_usage('sd'))
        p_help_str = str(h.show('sd'))
        self.assertEqual(usage, p_usage)
        self.assertLinesEqual(help_str, p_help_str)

    simple = "Description", "Footnotes", [
        'one, *, alpha', 'two, *, beta'
        ], ["""
        Func1 description

        one: one

        alpha: alpha
        """, """
        Func2 description

        two: two

        beta: beta
        """], [
        'sd --help [--usage]',
        'sd func1 --alpha=STR one',
        'sd func1 --help [--usage]',
        'sd func2 --beta=STR two',
        'sd func2 --help [--usage]',
        ], """
        Usage: sd command [args...]

        Description

        Commands:
          func1   Func1 description
          func2   Func2 description

        Footnotes
    """

    empty_docstring = None, None, [
        'one, *, alpha', 'two, *, beta'
        ], ['', ''], [
        'sd --help [--usage]',
        'sd func1 --alpha=STR one',
        'sd func1 --help [--usage]',
        'sd func2 --beta=STR two',
        'sd func2 --help [--usage]',
        ], """
        Usage: sd command [args...]

        Commands:
          func1
          func2
    """

    # TODO: change so that param: overrides a subcommand description
    complex_description = """
        This is a description.

        It has paragraphs:

            And code.

        param: but this should be ignored
        """, None, [''], [''], [
            'sd --help [--usage]',
            'sd func1 ',
            'sd func1 --help [--usage]',
        ], """
            Usage: sd command [args...]

            This is a description.

            It has paragraphs:

                And code.

            Commands:
              func1
        """

    def test_dummy_external(self):
        @runner.Clize.as_is
        def ext():
            raise NotImplementedError
        def func():
            raise NotImplementedError
        sd = runner.SubcommandDispatcher([ext, runner.Clize.as_is(func)])
        self._do_test(sd, [
            'sd --help [--usage]',
            'sd ext [args...]',
            'sd func [args...]',
        ], """
        Usage: sd command [args...]

        Commands:
          ext
          func
        """)

    def test_external_with_dummyhelp(self):
        @runner.Clize.as_is(description="Ext")
        def ext():
            raise NotImplementedError
        def func():
            raise NotImplementedError
        sd = runner.SubcommandDispatcher([
            ext,
            runner.Clize.as_is(func, description="Func")])
        self._do_test(sd, [
            'sd --help [--usage]',
            'sd ext [args...]',
            'sd func [args...]',
        ], """
        Usage: sd command [args...]

        Commands:
          ext    Ext
          func   Func
        """)

    def test_external_with_usage(self):
        @runner.Clize.as_is(usages=['ua abc', 'ub abc [def]'])
        def ext():
            raise NotImplementedError
        def func():
            raise NotImplementedError
        sd = runner.SubcommandDispatcher([
            ext,
            runner.Clize.as_is(func, usages=['uc --ab=STR', 'ud [--cd]'])])
        self._do_test(sd, [
            'sd --help [--usage]',
            'sd ext ua abc',
            'sd ext ub abc [def]',
            'sd func uc --ab=STR',
            'sd func ud [--cd]',
        ], """
        Usage: sd command [args...]

        Commands:
          ext
          func
        """)


class HelpUnitTests(unittest.TestCase):
    def test_compat_findall(self):
        document, _ = help._document_from_sphinx_docstring("some text", "a name", frontend)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wo_findall = list(help._findall_iter(OmitAttributes(document, {"findall"})))
        self.assertEqual(wo_findall, list(help._findall_iter(document)))

    def test_docutils_version_repr(self):
        self.assertEqual(
            repr(DocutilsVersion("a name", object())),
            "<a name>",
        )
