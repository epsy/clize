from sigtools import support

from clize import parser, extra, errors
from clize.tests import util


@util.testfunc
def check_repr(self, sig_str, annotation, str_rep):
    sig = support.s(sig_str, locals={'a': annotation})
    csig = parser.CliSignature.from_signature(sig)
    self.assertEqual(str(csig), str_rep)

@check_repr
class RepTests(object):
    mapped_basic = ('par:a', extra.mapped([
        ('greeting', ['hello'], 'h1'),
        ('parting', ['goodbye'], 'h2'),
        ]), 'par')
    mapped_force_icase = ('par:a', extra.mapped([
        (1, ['thing'], 'h')
        ], case_sensitive=False), 'par')
    mapped_force_scase = ('par:a', extra.mapped([
        (1, ['Thing'], 'h'),
        ], case_sensitive=True), 'par')
    mapped_imply_scase = ('par:a', extra.mapped([
        (1, ['thing'], 'h'),
        (2, ['Thing'], 'h'),
        ]), 'par')
    mapped_bad_icase = ('par:a', extra.mapped([
        (1, ['thing'], 'h'),
        (2, ['Thing'], 'h'),
        ], case_sensitive=False), 'par')

    oneof_basic = 'par:a', extra.one_of('hello', 'goodbye', 'bye'), 'par'
    oneof_help = 'par:a', extra.one_of(('hello', 'h1'), ('bye', 'h2')), 'par'


@util.testfunc
def annotated_sigtests(self, sig_info, in_args, args, kwargs):
    sig_str, annotation, str_rep = sig_info
    sig = support.s(sig_str, locals={'a': annotation})
    csig = parser.CliSignature.from_signature(sig)
    ba = csig.read_arguments(in_args)
    self.assertEqual(ba.args, args)
    self.assertEqual(ba.kwargs, kwargs)


@util.testfunc
def annotated_sigerror_tests(self, sig_info, in_args,
                             exc=errors.BadArgumentFormat):
    sig_str, annotation, str_rep = sig_info
    sig = support.s(sig_str, locals={'a': annotation})
    csig = parser.CliSignature.from_signature(sig)
    self.assertRaises(exc, csig.read_arguments, in_args)


@annotated_sigtests
class MappedTests(object):
    exact_1 = RepTests.mapped_basic, ['hello'], ['greeting'], {}
    exact_2 = RepTests.mapped_basic, ['goodbye'], ['parting'], {}
    isec_1 = RepTests.mapped_basic, ['HElLo'], ['greeting'], {}
    isec_2 = RepTests.mapped_basic, ['GoODByE'], ['parting'], {}

    forced_icase_1 = RepTests.mapped_force_icase, ['thing'], [1], {}
    forced_icase_2 = RepTests.mapped_force_icase, ['ThiNG'], [1], {}

    implied_scase_1 = RepTests.mapped_imply_scase, ['thing'], [1], {}
    implied_scase_2 = RepTests.mapped_imply_scase, ['Thing'], [2], {}

    forced_scase_1 = RepTests.mapped_force_scase, ['Thing'], [1], {}

    def test_show_list(self):
        sig = support.s('par:a', locals={'a': RepTests.mapped_basic[1]})
        csig = parser.CliSignature.from_signature(sig)
        ba = csig.read_arguments(['list'])
        par = csig.positional[0]
        self.assertEqual(par.show_list, ba.func)
        self.assertEqual(
            """name: Possible values for par:
            hello h1
            goodbye h2""".split(),
            ba.func('name', *ba.args, **ba.kwargs).split())


@annotated_sigerror_tests
class MappedErrorTests(object):
    not_found = RepTests.mapped_basic, ['dog']
    forced_scase = RepTests.mapped_force_scase, ['thing']
    bas_icase = RepTests.mapped_bad_icase, ['anything'], ValueError


@annotated_sigtests
class OneOfTests(object):
    exact = RepTests.oneof_basic, ('hello',), ['hello'], {}
    icase = RepTests.oneof_basic, ('Hello',), ['hello'], {}

    def test_show_list(self):
        sig = support.s('par:a', locals={'a': RepTests.oneof_help[1]})
        csig = parser.CliSignature.from_signature(sig)
        ba = csig.read_arguments(['list'])
        par = csig.positional[0]
        self.assertEqual(par.show_list, ba.func)
        self.assertEqual(
            """name: Possible values for par:
            hello h1
            bye h2""".split(),
            ba.func('name', *ba.args, **ba.kwargs).split())
