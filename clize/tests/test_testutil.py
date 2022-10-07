from clize.tests import util


class AssertLinesEqualTests(util.Fixtures):
    def _test(self, match, exp, real):
        if match:
            self.assertLinesEqual(exp, real)
        else:
            with self.assertRaises(AssertionError):
                self.assertLinesEqual(exp, real)


    empty = True, "", ""
    one_line = True, "message", "message"
    trailing_space = True, "message", "message   "
    trailing_newline = True, "message\n", "message\n"

    indent = True, """
        This is fine
            Subindent
    """, "This is fine\n    Subindent"

    one_different_line = False, "message", "telegram"
    differennt_indent = False, """
        This is fine
        This isn't indented
    """, "This is fine\n    This isn't indented"
