# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

from sigtools import support, modifiers, specifiers

from clize import parser, errors, util
from clize.tests.util import testfunc


@testfunc
def fromsigtests(self, sig_str, typ, str_rep, attrs):
    sig = support.s(sig_str, pre='from clize import Parameter')
    param = list(sig.parameters.values())[0]
    cparam = parser.CliSignature.convert_parameter(param)
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
    pos_default_int = 'one=3', parser.PositionalParameter, '[one]', {
        'typ': int, 'default': 3, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_but_required = (
        'one:Parameter.REQUIRED=3', parser.PositionalParameter, 'one', {
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

    alias = ('*, one: "a"', parser.OptionParameter, '-a STR',
        {'display_name': '--one', 'aliases': ['--one', '-a']})
    alias_shortest = ('*, one: "al"', parser.OptionParameter, '--al=STR',
        {'display_name': '--one', 'aliases': ['--one', '--al']})

    def test_alias_multi(self):
        sig = support.s('*, one: a', locals={'a': ('a', 'b', 'abc')})
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        self.assertEqual(type(cparam), parser.OptionParameter)
        self.assertEqual(str(cparam), '-a STR')
        self.assertEqual(cparam.display_name, '--one')
        self.assertEqual(cparam.aliases, ['--one', '-a', '-b', '--abc'])

    def test_param_inst(self):
        param = parser.Parameter('abc')
        sig = support.s('xyz: p', locals={'p': param})
        sparam = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(sparam)
        self.assertTrue(cparam is param)

    def test_converter(self):
        class CustExc(Exception):
            pass
        @parser.parameter_converter
        def converter(param, annotations):
            raise CustExc
        @parser.parameter_converter
        def noop_converter(param, annotations):
            pass

        sigs = [
            support.s('o: c', locals={'c': converter, 'n': noop_converter}),
            support.s('*, o: a',
                      locals={'a': ("abc", converter, noop_converter)})
            ]
        for sig in sigs:
            sparam = list(sig.parameters.values())[0]
            self.assertRaises(CustExc, parser.CliSignature.convert_parameter, sparam)


@testfunc
def signaturetests(self, sig_str, str_rep, args, posargs, kwargs):
    sig = support.s(sig_str, locals={'P': parser.Parameter})
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

    _two_str_a_usage = '-a STR -b STR'
    kw_short_nonglued = (
        '*, one: "a", two: "b"', _two_str_a_usage,
        ('-a', '1', '-b', '2'), [], {'one': '1', 'two': '2'})
    kw_short_glued = (
        '*, one: "a", two: "b"', _two_str_a_usage,
        ('-a1', '-b2'), [], {'one': '1', 'two': '2'})

    pos_and_kw = (
        'one, *, two, three, four: "a", five: "b"',
        '--two=STR --three=STR -a STR -b STR one',
        ('1', '--two', '2', '--three=3', '-a', '4', '-b5'),
        ['1'], {'two': '2', 'three': '3', 'four': '4', 'five': '5'})
    pos_and_kw_mixed = (
        'one, two, *, three', '--three=STR one two',
        ('1', '--three', '3', '2'), ['1', '2'], {'three': '3'}
        )

    flag = '*, one=False', '[--one]', ('--one',), [], {'one': True}
    flag_absent = '*, one=False', '[--one]', (), [], {}
    flag_glued = (
        '*, a=False, b=False, c=False', '[-a] [-b] [-c]',
        ('-ac',), [], {'a': True, 'c': True}
        )

    _one_flag = '*, one:"a"=False'
    _one_flag_u = '[-a]'
    flag_false = _one_flag, _one_flag_u, ('--one=',), [], {'one': False}
    flag_false_0 = _one_flag, _one_flag_u, ('--one=0',), [], {'one': False}
    flag_false_n = _one_flag, _one_flag_u, ('--one=no',), [], {'one': False}
    flag_false_f = _one_flag, _one_flag_u, ('--one=false',), [], {'one': False}

    collect_pos = '*args', '[args...]', ('1', '2', '3'), ['1', '2', '3'], {}
    pos_and_collect = (
        'a, *args', 'a [args...]',
        ('1', '2', '3'), ['1', '2', '3'], {})
    collect_and_kw = (
        '*args, one', '--one=STR [args...]',
        ('2', '--one', '1', '3'), ['2', '3'], {'one': '1'})

    conv = 'a=1', '[a]', ('1',), [1], {}

    named_int_glued = (
        '*, one:"a"=1, two:"b"="s"', '[-a INT] [-b STR]',
        ('-a15bham',), [], {'one': 15, 'two': 'ham'})

    double_dash = (
        'one, two, three', 'one two three',
        ('first', '--', '--second', 'third'),
        ['first', '--second', 'third'], {}
        )

    pos_last_option = (
        'one, two:P.L, *r, three', '--three=STR one two [r...]',
        ('1', '--three=3', '2', '--four', '4'),
        ['1', '2', '--four', '4'], {'three': '3'}
        )
    kw_last_option = (
        'one, two, *r, three:P.L', '--three=STR one two [r...]',
        ('1', '--three=3', '2', '--four', '4'),
        ['1', '2', '--four', '4'], {'three': '3'}
        )

    ignored = 'one:P.I', '', (), [], {}

    def test_converter_ignore(self):
        @parser.parameter_converter
        def conv(param, annotations):
            return parser.Parameter.IGNORE
        sig = support.s('one:conv', locals={'conv': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(str(csig), '')


@testfunc
def extraparamstests(self, sig_str, extra, args, posargs, kwargs, func):
    sig = support.s(sig_str)
    csig = parser.CliSignature.from_signature(sig, extra=extra)
    ba = csig.read_arguments(args)
    self.assertEqual(ba.args, posargs)
    self.assertEqual(ba.kwargs, kwargs)
    self.assertEqual(ba.func, func)


@extraparamstests
class ExtraParamsTests(object):
    _func = support.f('')
    alt_cmd = (
        '', [parser.AlternateCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', 'a', '-b', '--third'), ['a', '-b', '--third'], {}, _func
        )
    alt_cmd2 = (
        '', [parser.AlternateCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', '--alpha', '-b'), ['--alpha', '-b'], {}, _func
        )
    flb_cmd_start = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', '-a', 'b', '--third'), ['-a', 'b', '--third'], {}, _func
        )
    flb_cmd_valid = (
        '*a', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'b', '-c', '--fourth'), [], {}, _func
        )
    flb_cmd_invalid = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'a', '-b'), [], {}, _func
        )
    flb_cmd_invalid_valid = (
        'a: int, b',
        [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('xyz', 'abc', '--alt', 'def', '-g', '--hij'), [], {}, _func
        )

    def test_alt_middle(self):
        _func = support.f('')
        self.assertRaises(
            errors.ArgsBeforeAlternateCommand,
            self._test_func,
            '*a', [
                parser.AlternateCommandParameter(
                    func=_func, aliases=['--alt'])],
            ('a', '--alt', 'a', 'b'), ['a', 'b'], {}, _func
        )

    def test_param_extras(self):
        extra_params = [
            parser.FlagParameter(
                value=True, false_value=False,
                aliases=['-' + name], argument_name=name)
            for name in 'abc']
        param = parser.PositionalParameter(
            display_name='one', argument_name='one')
        param.extras = extra_params
        csig = parser.CliSignature([param])
        self.assertEqual('[-a] [-b] [-c] one', str(csig))


@testfunc
def sigerrortests(self, sig_str, args, exc_typ):
    sig = support.s(sig_str)
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
    unknown_kw_after_short_flag = '*, o=False', ['-oa'], errors.UnknownOption
    missing_value = '*, one', ['--one'], errors.MissingValue

    bad_format = 'one=1', ['a'], errors.BadArgumentFormat

    def test_not_enough_pos_collect(self):
        @modifiers.annotate(args=parser.Parameter.REQUIRED)
        def func(*args):
            raise NotImplementedError
        csig = parser.CliSignature.from_signature(
            specifiers.signature(func))
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
    sig = support.s(sig_str, pre='from clize import Parameter', locals=locals)
    params = list(sig.parameters.values())
    if len(params) != 1:
        raise ValueError("badparam requires exactly one parameter")
    try:
        parser.CliSignature.convert_parameter(params[0])
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
    alias_duplicate = '*, one: dup', {'dup': ('a', 'a')}
    unknown_annotation = 'one: ua', {'ua': UnknownAnnotation()}
    coerce_twice = 'one: co', {'co': (str, int)}
    dup_pconverter = 'one: a', {'a': (parser.default_converter,
                                      parser.default_converter)}
    unimplemented_parameter = '**kwargs',


@testfunc
def badsig(self, sig_str, locals=None):
    if locals is None:
        locals = {}
    sig = support.s(sig_str, pre='from clize import Parameter', locals=locals)
    try:
        parser.CliSignature.from_signature(sig)
    except ValueError:
        pass
    else:
        self.fail('ValueError not raised')


@badsig
class BadSigTests(object):
    alias_overlapping = '*, one: "a", two: "a"',
