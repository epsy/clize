from sigtools.test import f
from clize import runner, help
from clize.tests.util import testfunc

@testfunc
def test_whole_help(self, sig, doc, help_str):
    func = f(sig, pre="from clize import Parameter")
    func.__doc__ = doc
    r = runner.Clize(func)
    h = help.ClizeHelp(r, None)
    p_help_str = str(h.show('func'))
    self.assertEqual(p_help_str.split(), help_str.split())

@test_whole_help
class WholeHelpTests(object):
    simple = "one, *args, two", """
        Description

        one: Argument one

        args: Other arguments

        two: Option two

        Footer
    """, """
        Usage: func [OPTIONS] one [args...]

        Description

        Positional arguments:
            one     Argument one
            args    Other arguments

        Options:
            --two=STR   Option two

        Other actions:
            -h, --help  Show the help

        Footer
    """

    pos_out_of_order = "one, two", """
        Description

        two: Argument two

        one: Argument one
    """, """
        Usage: func one two

        Description

        Positional arguments:
            one     Argument one
            two     Argument two

        Other actions:
            -h, --help  Show the help
    """

    opt_out_of_order = "*, one, two", """
        two: Option two

        one: Option one
    """, """
        Usage: func [OPTIONS]

        Options:
            --two=STR   Option two
            --one=STR   Option one

        Other actions:
            -h, --help  Show the help
    """
