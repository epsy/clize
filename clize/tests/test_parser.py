from sigtools import test, modifiers
import inspect

from clize import parser, errors, util
from clize.tests.util import testfunc


@testfunc
def fromsigtests(self, sig_str, typ, str_rep, attrs):
    sig = test.s(sig_str, pre='from clize import Parameter')
    param = list(sig.parameters.values())[0]
    cparam = parser.Parameter.from_parameter(param)
    self.assertEqual(type(cparam), typ)
    self.assertEqual(str(cparam), str_rep)
    p_attrs = dict(
        (key, getattr(cparam, key))
        for key in attrs
        )
    self.assertEqual(p_attrs, attrs)


@fromsigtests
class FromSigTests(object):
    pos = 'one', parser.PositionalParameter, 'one', {
        'typ': util.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_str = 'one="abc"', parser.PositionalParameter, '[one]', {
        'typ': type("abc"), 'default': "abc", 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_none = 'one=None', parser.PositionalParameter, '[one]', {
        'typ': util.identity, 'default': None, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_int = 'one=3', parser.PositionalParameter, '[one=INT]', {
        'typ': int, 'default': 3, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_but_required = (
        'one:Parameter.REQUIRED=3', parser.PositionalParameter, 'one=INT', {
            'typ': int, 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': None})
    pos_last_option = (
        'one:Parameter.LAST_OPTION', parser.PositionalParameter, 'one', {
            'typ': util.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': True})

    collect = '*args', parser.ExtraPosArgsParameter, '[args...]', {
        'typ': util.identity, 'default': util.UNSET, 'required': False,
        'argument_name': 'args', 'display_name': 'args',
        'undocumented': False, 'last_option': None}
    collect_int = '*args:int', parser.ExtraPosArgsParameter, '[args...]', {
        'typ': int, 'default': util.UNSET, 'required': False,
        }
    collect_required = (
        '*args:Parameter.REQUIRED', parser.ExtraPosArgsParameter, 'args...', {
            'typ': util.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'args', 'display_name': 'args',
            'undocumented': False, 'last_option': None})

    named = '*, one', parser.OptionParameter, '--one=STR', {
        'typ': util.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}
    named_bool = '*, one=False', parser.FlagParameter, '[--one]', {
        }
    named_int = '*, one: int', parser.IntOptionParameter, '--one=INT', {
        'typ': int, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}

    alias = '*, one: "a"', parser.OptionParameter, '--one=STR', {
        'display_name': '--one', 'aliases': ['--one', '-a']}

    def test_param_inst(self):
        param = parser.Parameter('abc')
        sig = test.s('xyz: p', locals={'p': param})
        sparam = list(sig.parameters.values())[0]
        cparam = parser.Parameter.from_parameter(sparam)
        self.assertTrue(cparam is param)

@testfunc
def signaturetests(self, sig_str, str_rep, args, posargs, kwargs):
    sig = test.s(sig_str)
    csig = parser.CliSignature.from_signature(sig)
    ba = csig.read_arguments(args)
    self.assertEqual(str(csig), str_rep)
    self.assertEqual(ba.args, posargs)
    self.assertEqual(ba.kwargs, kwargs)

@signaturetests
class SigTests(object):
    pos = (
        'one, two, three', 'one two three',
        ('1', '2', '3'), ['1', '2', '3'], {})

    _two_str_usage = '--one=STR --two=STR'
    kw_glued = (
        '*, one, two', _two_str_usage,
        ('--one=1', '--two=2'), [], {'one': '1', 'two': '2'})
    kw_nonglued = (
        '*, one, two', _two_str_usage,
        ('--one', '1', '--two', '2'), [], {'one': '1', 'two': '2'})

    kw_short_nonglued = (
        '*, one: "a", two: "b"', _two_str_usage,
        ('-a', '1', '-b', '2'), [], {'one': '1', 'two': '2'})
    kw_short_glued = (
        '*, one: "a", two: "b"', _two_str_usage,
        ('-a1', '-b2'), [], {'one': '1', 'two': '2'})

    pos_and_kw = (
        'one, *, two, three, four: "a", five: "b"',
        '--two=STR --three=STR --four=STR --five=STR one',
        ('1', '--two', '2', '--three=3', '-a', '4', '-b5'),
        ['1'], {'two': '2', 'three': '3', 'four': '4', 'five': '5'})
    pos_and_kw_mixed = (
        'one, two, *, three', '--three=STR one two',
        ('1', '--three', '3', '2'), ['1', '2'], {'three': '3'}
        )

    flag = '*, one=False', '[--one]', ('--one',), [], {'one': True}
    flag_absent = '*, one=False', '[--one]', (), [], {}

    collect_pos = '*args', '[args...]', ('1', '2', '3'), ['1', '2', '3'], {}
    pos_and_collect = (
        'a, *args', 'a [args...]',
        ('1', '2', '3'), ['1', '2', '3'], {})
    collect_and_kw = (
        '*args, one', '--one=STR [args...]',
        ('2', '--one', '1', '3'), ['2', '3'], {'one': '1'})

    conv = 'a=1', '[a=INT]', ('1',), [1], {}

    named_int_glued = (
        '*, one:"a"=1, two:"b"="s"', '[--one=INT] [--two=STR]',
        ('-a15bham',), [], {'one': 15, 'two': 'ham'})

@testfunc
def extraparamstests(self, sig_str, extra, args, posargs, kwargs, func):
    sig = test.s(sig_str)
    csig = parser.CliSignature.from_signature(sig, extra=extra)
    ba = csig.read_arguments(args)
    self.assertEqual(ba.args, posargs)
    self.assertEqual(ba.kwargs, kwargs)
    self.assertEqual(ba.func, func)


@extraparamstests
class ExtraParamsTests(object):
    _func = test.f('')
    alt_cmd = (
        '', [parser.AlternateCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', 'a', 'b'), ['a', 'b'], {}, _func
        )
    flb_cmd_start = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', 'a', 'b'), ['a', 'b'], {}, _func
        )
    flb_cmd_valid = (
        '*a', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'b', 'c'), [], {}, _func
        )
    flb_cmd_invalid = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'a', 'b'), [], {}, _func
        )

    def test_alt_middle(self):
        _func = test.f('')
        self.assertRaises(
            errors.ArgsBeforeAlternateCommand,
            self._test_func,
            '*a', [
                parser.AlternateCommandParameter(
                    func=_func, aliases=['--alt'])],
            ('a', '--alt', 'a', 'b'), ['a', 'b'], {}, _func
        )


@testfunc
def sigerrortests(self, sig_str, args, exc_typ):
    sig = test.s(sig_str)
    csig = parser.CliSignature.from_signature(sig)
    try:
        csig.read_arguments(args)
    except exc_typ:
        pass
    except: #pragma: no cover
        raise
    else: #pragma: no cover
        self.fail('{0.__name__} not raised'.format(exc_typ))

@sigerrortests
class SigErrorTests(object):
    not_enough_pos = 'one, two', ['1'], errors.MissingRequiredArguments
    too_many_pos = 'one', ['1', '2'], errors.TooManyArguments

    missing_kw = '*, one', [], errors.MissingRequiredArguments
    duplicate_kw = (
        '*, one', ['--one', '1', '--one=1'], errors.DuplicateNamedArgument)
    unknown_kw = '', ['--one'], errors.UnknownOption
    missing_value = '*, one', ['--one'], errors.MissingValue

    bad_format = 'one=1', ['a'], errors.BadArgumentFormat

    def test_not_enough_pos_collect(self):
        @modifiers.annotate(args=parser.Parameter.REQUIRED)
        def func(*args):
            raise NotImplementedError
        csig = parser.CliSignature.from_signature(inspect.signature(func))
        try:
            csig.read_arguments(())
        except errors.MissingRequiredArguments:
            pass
        except: # pragma: no cover
            raise
        else:
            self.fail('MissingRequiredArguments not raised') # pragma: no cover

@testfunc
def badparam(self, sig_str, locals=None):
    if locals is None:
        locals = {}
    sig = test.s(sig_str, pre='from clize import Parameter', locals=locals)
    param = list(sig.parameters.values())[0]
    try:
        cparam = parser.Parameter.from_parameter(param)
    except ValueError:
        pass
    else:
        self.fail('ValueError not raised')

class UnknownAnnotation(object):
    pass

@badparam
class BadParamTests(object):
    alias_superfluous = 'one: "a"',
    alias_spaces = '*, one: "a b"',
    unknown_annotation = 'one: ua', {'ua': UnknownAnnotation()}
    coerce_twice = 'one: co', {'co': (str, int)}
