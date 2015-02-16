# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

from itertools import count

from sigtools.support import f
from sigtools.wrappers import wrapper_decorator

from clize import runner, help
from clize.tests.util import repeated_test

USAGE_HELP = 'func --help [--usage]'

@repeated_test
class WholeHelpTests(object):
    def _test_func(self, sig, doc, usage, help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func)
        h = help.ClizeHelp(r, None)
        h.prepare()
        p_usage = list(h.show_full_usage('func'))
        p_help_str = str(h.show('func'))
        self.assertEqual(usage, p_usage)
        self.assertEqual(help_str.split(), p_help_str.split())

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
            one     Argument one
            args... Other arguments

        Options:
            --two=STR   Option two

        Other actions:
            -h, --help  Show the help

        Footer
    """

    parens = "one:int, two=2, *args:int, alpha, beta:int, gamma=5", """
        Description

        one: Argument one

        two: Argument two

        args: Other arguments

        alpha: Option alpha

        beta: Option beta

        gamma: Option gamma

        Footer
    """, [
        'func --alpha=STR --beta=INT [--gamma=INT] one [two] [args...]',
        USAGE_HELP
    ], """
        Usage: func [OPTIONS] one [two] [args...]

        Description

        Arguments:
            one     Argument one (type: INT)
            two     Argument two (type: INT, default: 2)
            args... Other arguments (type: INT)

        Options:
            --alpha=STR  Option alpha
            --beta=INT   Option beta
            --gamma=INT  Option gamma (default: 5)

        Other actions:
            -h, --help  Show the help

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
            one     Argument one
            two     Argument two

        Other actions:
            -h, --help  Show the help
    """

    opt_out_of_order = "*, one, two", """
        two: Option two

        one: Option one
    """, ['func --one=STR --two=STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Options:
            --two=STR   Option two
            --one=STR   Option one

        Other actions:
            -h, --help  Show the help
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
            -h, --help  Show the help
    """

    short_name = '*, a', """
        a: alpha
    """, ['func -a STR', USAGE_HELP], """
        Usage: func [OPTIONS]

        Options:
            -a STR  alpha

        Other actions:
            -h, --help  Show the help
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
            --alpha=STR  Stuff

        Formatting options:
            --beta=STR  Other stuff

        Other actions:
            -h, --help  Show the help
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
            --alpha=STR  Stuff
            --beta=STR  Other stuff

        Other actions:
            -h, --help  Show the help
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
            --alpha=STR  Stuff
            --beta=STR  Other stuff

        Other actions:
            -h, --help  Show the help
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
            one     Argument one
            two     Argument two
            args... Other arguments

        Label:
            --alpha=STR   Option alpha

        Other actions:
            -h, --help  Show the help

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
            one     Argument one
            two     Argument two

        Options:
            --alpha=STR   Option alpha

        Other actions:
            -h, --help  Show the help

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
            one     Argument one

        after one

            two     Argument two

        after two

        Options:
            --alpha=STR   Option alpha

        after alpha

            --beta=STR   Option beta

        after beta

        Other actions:
            -h, --help  Show the help

        Footer
    """
    undocumented = "one:P.U, two:P.U, *args:P.U, alpha:P.U, beta:P.U", """
        Description

        two: unseen

        beta: unseen

        Footer
    """, ['func ', USAGE_HELP], """
        Usage: func [OPTIONS]

        Description

        Other actions:
        -h, --help  Show the help

        Footer
    """


@repeated_test
class WrappedFuncTests(object):
    def _test_func(self, sig, wrapper_sigs, doc, wrapper_docs, help_str):
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
        self.assertEqual(help_str.split(), p_help_str.split())

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
            -h, --help  Show the help
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
            two     Two
            three   Three
            one     One

        Options:
            --alpha=STR Alpha
            --beta=STR  Beta
            --gamma=STR Gamma

        Other actions:
            -h, --help  Show the help
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
            two     Two
            three   Three
            one     One

        Options:
            --alpha=STR Alpha

        Label beta:
            --beta=STR  Beta

        Label gamma:
            --gamma=STR Gamma

        Other actions:
            -h, --help  Show the help
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
            two     Two
            three   Three
            one     One

        Options:
            --alpha=STR Alpha

        Label:
            --beta=STR  Beta
            --gamma=STR Gamma

        Other actions:
            -h, --help  Show the help
    """


@repeated_test
class FormattingTests(object):
    def _test_func(self, sig, doc, help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func)
        h = help.ClizeHelp(r, None)
        h.prepare()
        p_help_str = str(h.show('func'))
        self.assertEqual(help_str, p_help_str)

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


@repeated_test
class DispatcherHelper(object):
    def _test_func(self, description, footer, sigs, docs, usage, help_str):
        funcs = []
        for i, sig, doc in zip(count(1), sigs, docs):
            func = f(sig)
            func.__doc__ = doc
            func.__name__ = 'func' + str(i)
            funcs.append(func)
        sd = runner.SubcommandDispatcher(funcs, description, footer)
        h = sd.cli.helper
        h.prepare()
        p_usage = list(h.show_full_usage('sd'))
        p_help_str = str(h.show('sd'))
        self.assertEqual(usage, p_usage)
        self.assertEqual(help_str.split(), p_help_str.split())

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
