# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import __future__
import sys
import pathlib
import unittest

from sigtools import support, modifiers, specifiers

from clize import parser, errors, util
from clize.tests.util import Fixtures


_ic = parser._implicit_converters


class FromSigTests(Fixtures):
    def _test(self, sig_str, typ, str_rep, attrs):
        pre_code = "import pathlib; from clize import Parameter"
        sig = self._support_s(sig_str, pre=pre_code)
        return self._do_test(sig, typ, str_rep, attrs)

    def _do_test(self, sig, typ, str_rep, attrs):
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        self.assertEqual(type(cparam), typ)
        self.assertEqual(str(cparam), str_rep)
        p_attrs = dict(
            (key, getattr(cparam, key))
            for key in attrs
            )
        self.assertEqual(p_attrs, attrs)

    def _support_s(self, *args, **kwargs):
        return support.s(*args, **kwargs)

    pos = 'one', parser.PositionalParameter, 'one', {
        'conv': parser.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_str = 'one="abc"', parser.PositionalParameter, '[one]', {
        'conv': parser.identity, 'default': "abc", 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_none = 'one=None', parser.PositionalParameter, '[one]', {
        'conv': parser.identity, 'default': None, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_int = 'one=3', parser.PositionalParameter, '[one]', {
        'conv': _ic[int], 'default': 3, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_path = (
        'file=pathlib.Path(\'/tmp\')', parser.PositionalParameter, '[file]', {
            'conv': _ic[pathlib.PurePath],
            'default': pathlib.Path('/tmp'), 'argument_name': 'file',
            'required': False, 'undocumented': False,
            'last_option': None, 'display_name': 'file'})
    pos_default_but_required = (
        'one:Parameter.REQUIRED=3', parser.PositionalParameter, 'one', {
            'conv': _ic[int], 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': None})
    pos_last_option = (
        'one:Parameter.LAST_OPTION', parser.PositionalParameter, 'one', {
            'conv': parser.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': True})

    collect = '*args', parser.ExtraPosArgsParameter, '[args...]', {
        'conv': parser.identity, 'default': util.UNSET, 'required': False,
        'argument_name': 'args', 'display_name': 'args',
        'undocumented': False, 'last_option': None}
    collect_int = '*args:int', parser.ExtraPosArgsParameter, '[args...]', {
        'conv': _ic[int], 'default': util.UNSET, 'required': False,
        }
    collect_required = (
        '*args:Parameter.REQUIRED', parser.ExtraPosArgsParameter, 'args...', {
            'conv': parser.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'args', 'display_name': 'args',
            'undocumented': False, 'last_option': None})

    named = '*, one', parser.OptionParameter, '--one=STR', {
        'conv': parser.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}
    named_bool = '*, one=False', parser.FlagParameter, '[--one]', {
        }
    named_int = '*, one: int', parser.IntOptionParameter, '--one=INT', {
        'conv': _ic[int], 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}

    alias = ('*, one: "a"', parser.OptionParameter, '-a STR',
        {'display_name': '--one', 'aliases': ['--one', '-a']})
    alias_shortest = ('*, one: "al"', parser.OptionParameter, '--al=STR',
        {'display_name': '--one', 'aliases': ['--one', '--al']})

    def test_vconverter(self):
        @parser.value_converter
        def converter(value):
            raise NotImplementedError
        sig = self._support_s('*, par: conv', globals={'conv': converter})
        self._do_test(sig, parser.OptionParameter, '--par=CONVERTER', {
            'conv': converter,
            })

    def test_default_type(self):
        @parser.value_converter
        class FancyDefault(object):
            def __init__(self, arg):
                self.arg = arg
        deft = FancyDefault('ham')
        sig = self._support_s('*, par=default', globals={'default': deft})
        self._do_test(sig, parser.OptionParameter, '[--par=FANCYDEFAULT]', {
            'conv': FancyDefault,
            'default': deft,
        })

    def test_bad_default_good_conv(self):
        class UnknownDefault(object):
            pass
        deft = UnknownDefault()
        sig = self._support_s('*, par:str=default', globals={'default': deft})
        self._do_test(sig, parser.OptionParameter, '[--par=STR]', {
            'conv': parser.identity,
            'default': deft,
        })

    def test_method_conv(self):
        class Spam(object):
            def method(self, arg):
                return self
        s = Spam()
        conv = parser.value_converter(s.method, name='TCONV')
        sig = self._support_s('*, par: conv', globals={'conv': conv})
        self._do_test(sig, parser.OptionParameter, '--par=TCONV', {
            'conv': conv
        })
        csig = parser.CliSignature.from_signature(sig)
        ba = self.read_arguments(csig, ['--par=arg'])
        arg = ba.kwargs['par']
        self.assertTrue(arg is s)

    def test_flagp_conv_long(self):
        @parser.value_converter
        def conv(arg):
            return arg
        param = parser.FlagParameter(
            argument_name='par',
            value='eggs', conv=conv,
            aliases=['--par']
            )
        self.assertEqual(param.get_all_names(), '--par[=CONV]')
        sig = self._support_s('*, par: p, o=False', globals={'p': param})
        self._do_test(sig, parser.FlagParameter, '[--par[=CONV]]', {
            'conv': conv,
        })
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(self.read_arguments(csig, []).kwargs, {})
        self.assertEqual(self.read_arguments(csig, ['--par']).kwargs,
                         {'par': 'eggs'})
        self.assertEqual(self.read_arguments(csig, ['--par=ham']).kwargs,
                         {'par': 'ham'})

    def test_flagp_conv_short(self):
        @parser.value_converter
        def conv(arg):
            raise NotImplementedError
        param = parser.FlagParameter(
            argument_name='par',
            value='eggs', conv=conv,
            aliases=['--par', '-p']
            )
        self.assertEqual(param.get_all_names(), '-p, --par[=CONV]')
        sig = self._support_s('*, par: p, o=False', globals={'p': param})
        self._do_test(sig, parser.FlagParameter, '[-p]', {
            'conv': conv,
        })
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(self.read_arguments(csig, []).kwargs, {})
        self.assertEqual(self.read_arguments(csig, ['-p']).kwargs,
                         {'par': 'eggs'})
        self.assertEqual(self.read_arguments(csig, ['-po']).kwargs,
                         {'par': 'eggs', 'o': True})

    def test_alias_multi(self):
        sig = self._support_s('*, one: a', globals={'a': ('a', 'b', 'abc')})
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        self.assertEqual(type(cparam), parser.OptionParameter)
        self.assertEqual(str(cparam), '-a STR')
        self.assertEqual(cparam.display_name, '--one')
        self.assertEqual(cparam.aliases, ['--one', '-a', '-b', '--abc'])

    def test_param_inst(self):
        param = parser.Parameter('abc')
        sig = self._support_s('xyz: p', globals={'p': param})
        sparam = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(sparam)
        self.assertTrue(cparam is param)

    def test_pconverter(self):
        class CustExc(Exception):
            pass
        @parser.parameter_converter
        def converter(param, annotations):
            raise CustExc
        @parser.parameter_converter
        def noop_converter(param, annotations):
            raise NotImplementedError

        sigs = [
            self._support_s('o: c', globals={'c': converter}),
            self._support_s('*, o: a', globals={'a': ("abc", converter)})
            ]
        for sig in sigs:
            sparam = list(sig.parameters.values())[0]
            self.assertRaises(CustExc, parser.CliSignature.convert_parameter, sparam)

    def test_parameterflag_repr(self):
        f1 = parser.ParameterFlag('someflag')
        self.assertEqual(repr(f1), 'clize.Parameter.someflag')
        f2 = parser.ParameterFlag('someflag', 'someobject')
        self.assertEqual(repr(f2), 'someobject.someflag')


class SigTests(Fixtures):
    def _test(self, sig_str, *args, **kwargs):
        sig = support.s(sig_str, globals={'P': parser.Parameter})
        self._do_test(sig, *args, **kwargs)

    def _do_test(self, sig, str_rep, args, posargs, kwargs):
        csig = parser.CliSignature.from_signature(sig)
        ba = self.read_arguments(csig, args)
        self.assertEqual(str(csig), str_rep)
        self.assertEqual(ba.args, posargs)
        self.assertEqual(ba.kwargs, kwargs)
        repr(ba) # ensure attrs repr does't crash

    no_param = '', '', (), [], {}

    pos = (
        'one, two, three', 'one two three',
        ('1', '2', '3'), ['1', '2', '3'], {})

    pos_empty = (
        'one', 'one',
        ('',), [''], {}
        )

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
    kw_short_case = (
        '*, one: "a", two: "A"', '-a STR -A STR',
        ('-a', 'one', '-A', 'two'), [], {'one': 'one', 'two': 'two'})

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
    named_int_glued_negative = (
        '*, one:"a"=1, two:"b"="s"', '[-a INT] [-b STR]',
        ('-a-23bham',), [], {'one': -23, 'two': 'ham'})
    named_int_last = (
        '*, one:"a"=1', '[-a INT]',
        ('-a23',), [], {'one': 23})

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
        sig = support.s('one:conv', globals={'conv': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(str(csig), '')

    def test_namedparams_alter(self):
        param = parser.OptionParameter(aliases=['--new'], argument_name='new')
        class ParamInserter(parser.FlagParameter):
            def __init__(self, **kwargs):
                super(ParamInserter, self).__init__(value=True, argument_name=None, **kwargs)
            def read_argument(self, ba, i):
                ba.namedparams['--new'] = param
        csig = parser.CliSignature([ParamInserter(aliases=['--insert'])])

        with self.assertRaises(errors.UnknownOption):
            csig.read_arguments(['--new', 'abc'], 'test')
        ba = csig.read_arguments(['--insert', '--new', 'abc'], 'test')
        self.assertEqual(ba.kwargs, {'new': 'abc'})
        with self.assertRaises(errors.UnknownOption):
            csig.read_arguments(['--new', 'abc'], 'test')

    def test_posparam_set_value_parameter_not_present(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two')
        sig = support.s('one, two')
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=['one', 'two'])
        with self.assertRaises(ValueError):
            param.set_value(ba, 'inserted')

    def test_posparam_set_value_only(self):
        param = parser.PositionalParameter(argument_name='one', display_name='one')
        sig = support.s('one:par', globals={'par': param})
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=[])
        param.set_value(ba, 'inserted')
        self.assertEqual(ba.args, ['inserted'])

    def test_posparam_set_value_already_set(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two')
        sig = support.s('one, two:par', globals={'par': param})
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=['one', 'two'])
        param.set_value(ba, 'inserted')
        self.assertEqual(ba.args, ['one', 'inserted'])

    def test_posparam_set_value_after_set(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two')
        sig = support.s('one, two:par', globals={'par': param})
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=['one'])
        param.set_value(ba, 'inserted')
        self.assertEqual(ba.args, ['one', 'inserted'])

    def test_posparam_set_value_after_default(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two', default="two")
        sig = support.s('one="one", two:par="two"', globals={'par': param})
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=[])
        param.set_value(ba, 'inserted')
        self.assertEqual(ba.args, ['one', 'inserted'])

    def test_posparam_set_value_after_missing(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two')
        sig = support.s('one, two:par', globals={'par': param})
        csig = parser.CliSignature.from_signature(sig)
        ba = parser.CliBoundArguments(csig, [], 'func', args=[])
        with self.assertRaises(ValueError):
            param.set_value(ba, 'inserted')

    def test_vconverter_keep_default(self):
        @parser.value_converter
        def conv(arg):
            return 'converted'
        sig = support.s('*, par:conv="default"', globals={'conv': conv})
        self._do_test(sig, '[--par=CONV]', (), [], {})

    def test_vconverter_convert_value(self):
        @parser.value_converter(convert_default=True)
        def conv(arg):
            return 'c{}c'.format(arg)
        sig = support.s('*, par:conv="default"', globals={'conv': conv})
        self._do_test(sig, '[--par=CONV]', ('--par=A',), [], {'par': 'cAc'})
        self._do_test(sig, '[--par=CONV]', ('--par', 'A',), [], {'par': 'cAc'})

    def test_vconverter_convert_default(self):
        @parser.value_converter(convert_default=True)
        def conv(arg):
            return 'converted'
        sig = support.s('*, par:conv="default"', globals={'conv': conv})
        self._do_test(sig, '[--par=CONV]', (), [], {'par': 'converted'})

    def test_vconverter_convert_default_after_pos(self):
        @parser.value_converter(convert_default=True)
        def conv(arg):
            return 'converted'
        sig = support.s('first="otherdefault", par:conv="default"', globals={'conv': conv})
        self._do_test(sig, '[first] [par]', (), ['otherdefault', 'converted'], {})


class ExtraParamsTests(Fixtures):
    def _test(self, sig_str, extra, args, posargs, kwargs, func):
        sig = support.s(sig_str)
        csig = parser.CliSignature.from_signature(sig, extra=extra)
        ba = self.read_arguments(csig, args)
        self.assertEqual(ba.args, posargs)
        self.assertEqual(ba.kwargs, kwargs)
        self.assertEqual(ba.func, func)

    _func = support.f('')
    _func2 = support.f('')

    alt_cmd = (
        '', [parser.AlternateCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', 'a', '-b', '--third'),
        ['test --alt', 'a', '-b', '--third'], {}, _func
        )
    alt_cmd2 = (
        '', [parser.AlternateCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', '--alpha', '-b'),
        ['test --alt', '--alpha', '-b'], {}, _func
        )
    flb_cmd_start = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('--alt', '-a', 'b', '--third'),
        ['test --alt', '-a', 'b', '--third'], {}, _func
        )
    flb_cmd_valid = (
        '*a', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'b', '-c', '--fourth'),
        ['test --alt'], {}, _func
        )
    flb_cmd_invalid = (
        '', [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('a', '--alt', 'a', '-b'),
        ['test --alt'], {}, _func
        )
    flb_cmd_invalid_valid = (
        'a: int, b',
        [parser.FallbackCommandParameter(func=_func, aliases=['--alt'])],
        ('xyz', 'abc', '--alt', 'def', '-g', '--hij'),
        ['test --alt'], {}, _func
        )
    flb_after_alt = (
        'a: int, b',
        [
            parser.AlternateCommandParameter(func=_func, aliases=['--alt']),
            parser.FallbackCommandParameter(func=_func2, aliases=['--flb']),
        ],
        ('--invalid', '--alt', '--flb'),
        ['test --flb'], {}, _func2
        )

    def test_alt_middle(self):
        _func = support.f('')
        args = [
            '*a', [
                parser.AlternateCommandParameter(
                    func=_func, aliases=['--alt'])],
            ('a', '--alt', 'a', 'b'), ['a', 'b'], {}, _func
            ]
        exp_msg = ('Error: Arguments found before alternate '
                   'action parameter --alt')
        with self.assertRaisesRegex(errors.ArgsBeforeAlternateCommand, exp_msg):
            self._test(*args)

    def test_param_extras(self):
        extra_params = [
            parser.FlagParameter(
                value=True, conv=parser.is_true,
                aliases=['-' + name], argument_name=name)
            for name in 'abc']
        param = parser.PositionalParameter(
            display_name='one', argument_name='one')
        param.extras = extra_params
        csig = parser.CliSignature([param])
        self.assertEqual('[-a] [-b] [-c] one', str(csig))



class SigErrorTests(Fixtures):
    def _test(self, sig_str, args, exc_typ, message):
        sig = support.s(sig_str)
        csig = parser.CliSignature.from_signature(sig)
        with self.assertRaisesRegex(exc_typ, 'Error: ' + message):
            self.read_arguments(csig, args)

    not_enough_pos = (
        'one, two', ['1'], errors.MissingRequiredArguments,
        'Missing required arguments: two')
    too_many_pos = (
        'one', ['1', '2'], errors.TooManyArguments,
        'Received extra arguments: 2')

    missing_kw = (
        '*, one', [], errors.MissingRequiredArguments,
        'Missing required arguments: --one')
    duplicate_opt = (
        '*, one', ['--one', '1', '--one=1'], errors.DuplicateNamedArgument,
        '--one was specified more than once')
    duplicate_intopt = (
        '*, one=1', ['--one', '1', '--one=1'], errors.DuplicateNamedArgument,
        '--one was specified more than once')
    unknown_kw = (
        '', ['--one'], errors.UnknownOption,
        'Unknown option \'--one\'')
    unknown_kw_after_short_flag = (
        '*, o=False', ['-oa'], errors.UnknownOption,
        'Unknown option \'-a\'')
    unknown_kv_guess = (
        '*, bar', ['--baa'], errors.UnknownOption,
        'Unknown option \'--baa\'\\. Did you mean \'--bar\'\\?')
    unknown_kw_no_guess = (
        '*, bar', ['--foo'], errors.UnknownOption,
        'Unknown option \'--foo\'')
    original_name_guess = (
        '*, thisOption', ['--thisOption'], errors.UnknownOption,
        'Unknown option \'--thisOption\'\\. Did you mean \'--this-option\'\\?')
    missing_value = (
        '*, one', ['--one'], errors.MissingValue,
        'No value found after --one')

    bad_format = (
        'one=1', ['a'], errors.BadArgumentFormat, 'Bad value for one: \'a\'')

    def test_not_enough_pos_collect(self):
        @modifiers.annotate(args=parser.Parameter.REQUIRED)
        def func(*args):
            raise NotImplementedError
        csig = parser.CliSignature.from_signature(
            specifiers.signature(func))
        with self.assertRaises(errors.MissingRequiredArguments):
            self.read_arguments(csig, ())


has_future_annotations = (
    hasattr(__future__, "annotations")
    and sys.version_info < (3, 11, 0, "final")
)


@unittest.skipUnless(has_future_annotations, "__future__.annotations only available certain python versions")
class FromSigTestsStringAnnotations(FromSigTests):
    def _test(self, *args, **kwargs):
        return super()._test(*args, **kwargs)

    def _support_s(self, *args, **kwargs):
        return super()._support_s(*args, future_features=("annotations",), **kwargs)


class UnknownAnnotation(object):
    pass


class UnknownDefault(object):
    def __init__(self, arg):
        self.arg = arg


class BadParamTests(Fixtures):
    def _test(self, sig_str, globals, exp_msg):
        sig = support.s(sig_str, pre='from clize import Parameter', globals=globals)
        params = list(sig.parameters.values())
        with self.assertRaises(ValueError) as ar:
            parser.CliSignature.convert_parameter(params[0])
        if exp_msg is not None:
            self.assertEqual(exp_msg, str(ar.exception))

    alias_superfluous = 'one: "a"', {}, "Cannot give aliases for a positional parameter."
    alias_spaces = '*, one: "a b"', {}, "Cannot have whitespace in aliases."
    alias_duplicate = '*, one: dup', {'dup': ('a', 'a')}, "Duplicate alias 'a'"
    _ua = UnknownAnnotation()
    unknown_annotation = (
        'one: ua', {'ua': _ua}, "Unknown annotation " + repr(_ua) + "\n"
        "If you intended for it to be a value or parameter converter, "
        "make sure the appropriate decorator was applied.")
    def _uc(arg):
        raise NotImplementedError
    unknown_callable = (
        'one: uc', {'uc': _uc}, "Unknown annotation " + repr(_uc) + "\n"
        "If you intended for it to be a value or parameter converter, "
        "make sure the appropriate decorator was applied.")
    _ud = UnknownDefault('stuff')
    bad_custom_default = (
        'one=bd', {'bd': _ud},
        "Cannot find value converter for default value " + repr(_ud) + ". "
        "Please specify one as an annotation.\n"
        "If the default value's type should be used to convert the value, "
        "make sure it is decorated with clize.parser.value_converter()")
    coerce_twice = 'one: co', {'co': (str, int)}, "Value converter specified twice in annotation: str int"
    dup_pconverter = (
        'one: a',
        {'a': (parser.default_converter, parser.default_converter)},
        "Parameter converter 'default_converter' must be the first "
        "element of a parameter's annotation")
    unimplemented_parameter = (
        '**kwargs', {},
        "This converter cannot convert parameter 'kwargs' to a CLI parameter")



class BadSigTests(Fixtures):
    def _test(self, sig_str):
        sig = support.s(sig_str, pre='from clize import Parameter')
        self.assertRaises(ValueError, parser.CliSignature.from_signature, sig)

    alias_overlapping = '*, one: "a", two: "a"',
