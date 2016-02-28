# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from itertools import count

from sigtools.support import f
from sigtools.modifiers import autokwoargs
from sigtools.wrappers import wrapper_decorator

from clize import runner, help, parser, util
from clize.tests.util import Fixtures, tup

USAGE_HELP = 'func --help [--usage]'


class WholeHelpTests(Fixtures):
    def _test(self, sig, doc, usage, help_str):
        func = f(sig, pre="from clize import Parameter as P")
        func.__doc__ = doc
        r = runner.Clize(func)
        self._do_test(r, usage, help_str)

    def _do_test(self, runner, usage, help_str):
        h = help.ClizeHelp(runner, None)
        h.prepare()
        pc_usage = h.cli('func --help', '--usage')
        p_usage = [l.rstrip() for l in h.show_full_usage('func')]
        pc_help_str = h.cli('func --help')
        p_help_str = str(h.show('func'))
        self.assertEqual(usage, p_usage)
        self.assertEqual('\n'.join(usage), pc_usage)
        self.assertEqual(help_str.split(), p_help_str.split())
        self.assertEqual(help_str.split(), pc_help_str.split())

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
            one     Argument one (type: INT)
            two     Argument two (type: INT, default: 2)
            three   Argument three
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
    undocumented_all = "one:P.U, two:P.U, *args:P.U, alpha:P.U, beta:P.U", """
        Description

        two: unseen

        beta: unseen

        Footer
    """, ['func', USAGE_HELP], """
        Usage: func [OPTIONS]

        Description

        Other actions:
        -h, --help  Show the help

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
        -6  Use IPv6?

        Other actions:
        -h, --help  Show the help

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
            --alt
            -h, --help  Show the help
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
            locals={'a': parser.use_class(named=CustParam)})
        func.__doc__ = """
            param: Param desc

            After param

            _:_

        """
        r = runner.Clize(func)
        self._do_test(r, ['func --param=STR', USAGE_HELP], """
            Usage: func [OPTIONS]

            Options:
                I am    a custom parameter!

            There is stuff after me.

            Param desc

            After param

            Other actions:
                -h, --help  Show the help
        """)



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


class AutoforwardedFuncTests(Fixtures):
    def _test(self, func, help_str):
        r = runner.Clize(func)
        h = help.ClizeHelp(r, None)
        h.prepare()
        p_help_str = str(h.show('func'))
        self.assertEqual(help_str.split(), p_help_str.split())

    def _decorator(func):
        @autokwoargs
        def _wrapper(one, two, three=3, *args, **kwargs):
            """
            one: param one

            two: param two

            three: param three
            """
            func(*args, **kwargs)
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two alpha beta
        Description

        Arguments:
        one     param one
        two     param two
        alpha   param alpha
        beta    param beta

        Options:
        --gamma=STR     param gamma
        --three=INT     param three (default: 3)

        Other actions:
        -h, --help      Show the help
    """)
    @_decorator
    @autokwoargs
    def decorated(alpha, beta, gamma=None):
        """
        Description

        alpha: param alpha

        beta: param beta

        gamma: param gamma
        """
        return alpha, beta, gamma


    def _decorator(func):
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
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two beta
        description in func

        Arguments:
        one     param one
        two     param two
        beta

        Options:
        --gamma=STR     param gamma
        --three=INT     param three (default: 3)

        Label:
        --four=INT      param four (default: 4)

        Other actions:
        -h, --help      Show the help
    """)
    @_decorator
    @autokwoargs
    def messy_docstrings(one, beta, gamma=None):
        """
        description in func

        one: param alpha

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
        return _wrapper

    @tup("""
        Usage: func [OPTIONS] one two four five alpha beta
        description in func
        description in decorator A
        description in decorator B

        Arguments:
        one     param one
        free in decorator A after one
        two     param two
        free in decorator A after two
        four    param four
        free in decorator B after four
        five    param five
        free in decorator B after five
        alpha   param alpha
        free in func after alpha
        beta    param beta
        free in func after beta

        Options:
        --gamma=STR     param gamma
        free in func after gamma
        --three=INT     param three (default: 3)
        free in decorator A after three
        --six=INT       param six (default: 6)
        free in decorator B after six

        Other actions:
        -h, --help      Show the help

        footnotes in func
        footnotes in decorator A
        footnotes in decorator B
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
            ext     Ext
            func    Func
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
