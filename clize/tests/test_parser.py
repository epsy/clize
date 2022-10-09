# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.
import functools
import inspect
import os
import pathlib
import typing
import warnings

import repeated_test
from repeated_test import evaluated, options
from sigtools import support, modifiers, specifiers

from clize import parser, errors, util, Clize, Parameter
from clize.tests.util import Fixtures, SignatureFixtures


_ic = parser._implicit_converters


def skip_unless(condition, message):
    @evaluated
    def _skip_unless(self, **_):
        if not condition:
            self.skipTest(message)
        else:
            return ()
    return _skip_unless


skip_unless_typings_has_annotations = skip_unless(
    hasattr(typing, "Annotated"),
    "This test needs typing.Annotated"
)


def defer(func):
    @evaluated
    def _deferred(*_, **__):
        return func()
    return _deferred


def s(sig_str, **inject):
    @evaluated
    def evaluate_sig(self, *, make_signature, **_):
        pre_code = (
            "import pathlib;"
            "from clize import *;"
            "import typing;"
            "P = Parameter;"
        )
        return make_signature(sig_str, pre=pre_code, globals=dict(inject)),
    return evaluate_sig


class FromSigTests(SignatureFixtures):
    def _test(self, sig, typ, str_rep, attrs, *, make_signature):
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        self.assertEqual(type(cparam), typ)
        self.assertEqual(str(cparam), str_rep)
        p_attrs = dict(
            (key, getattr(cparam, key))
            for key in attrs
            )
        self.assertEqual(p_attrs, attrs)

    pos = s('one'), parser.PositionalParameter, 'one', {
        'conv': parser.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_str = s('one="abc"'), parser.PositionalParameter, '[one]', {
        'conv': parser.identity, 'default': "abc", 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_none = s('one=None'), parser.PositionalParameter, '[one]', {
        'conv': parser.identity, 'default': None, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_int = s('one=3'), parser.PositionalParameter, '[one]', {
        'conv': _ic[int], 'default': 3, 'required': False,
        'argument_name': 'one', 'display_name': 'one',
        'undocumented': False, 'last_option': None}
    pos_default_path = (
        s('file=pathlib.Path(\'/tmp\')'), parser.PositionalParameter, '[file]', {
            'conv': _ic[pathlib.PurePath],
            'default': pathlib.Path('/tmp'), 'argument_name': 'file',
            'required': False, 'undocumented': False,
            'last_option': None, 'display_name': 'file'})
    pos_default_but_required = (
        s('one:Parameter.REQUIRED=3'), parser.PositionalParameter, 'one', {
            'conv': _ic[int], 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': None})
    pos_last_option = (
        s('one:Parameter.LAST_OPTION'), parser.PositionalParameter, 'one', {
            'conv': parser.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'one', 'display_name': 'one',
            'undocumented': False, 'last_option': True})

    collect = s('*args'), parser.ExtraPosArgsParameter, '[args...]', {
        'conv': parser.identity, 'default': util.UNSET, 'required': False,
        'argument_name': 'args', 'display_name': 'args',
        'undocumented': False, 'last_option': None}
    collect_int = s('*args:int'), parser.ExtraPosArgsParameter, '[args...]', {
        'conv': _ic[int], 'default': util.UNSET, 'required': False,
        }
    collect_required = (
        s('*args:Parameter.REQUIRED'), parser.ExtraPosArgsParameter, 'args...', {
            'conv': parser.identity, 'default': util.UNSET, 'required': True,
            'argument_name': 'args', 'display_name': 'args',
            'undocumented': False, 'last_option': None})

    named = s('*, one'), parser.OptionParameter, '--one=STR', {
        'conv': parser.identity, 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}
    named_bool = s('*, one=False'), parser.FlagParameter, '[--one]', {
        }
    named_int = s('*, one: int'), parser.IntOptionParameter, '--one=INT', {
        'conv': _ic[int], 'default': util.UNSET, 'required': True,
        'argument_name': 'one', 'display_name': '--one', 'aliases': ['--one'],
        'undocumented': False, 'last_option': None}

    alias = (s('*, one: "a"'), parser.OptionParameter, '-a STR',
        {'display_name': '--one', 'aliases': ['--one', '-a']})
    alias_shortest = (s('*, one: "al"'), parser.OptionParameter, '--al=STR',
        {'display_name': '--one', 'aliases': ['--one', '--al']})

    typed_alias_named = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[int, Clize['a']]),
        parser.IntOptionParameter, '-a INT', {
            "display_name": "--one",
            "aliases": ["--one", "-a"],
            "conv": _ic[int],
        }))

    typed_known_but_overridden = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[str, Clize[int]]),
        parser.IntOptionParameter, '--one=INT', {
            "conv": _ic[int],
        }
    ))

    typed_unknown_but_overridden = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[typing.Union[int, str], Clize[int]]),
        parser.IntOptionParameter, '--one=INT', {
            "conv": _ic[int],
        }
    ))

    typed_has_unknown_metadata = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[str, 'a', Clize['b']]),
        parser.OptionParameter, '-b STR', {
            "conv": _ic[str],
        }
    ))

    typed_doubly_annotated = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[str, typing.Annotated[int, Clize['a']]]),
        parser.OptionParameter, '-a STR', {
            "conv": _ic[str],
        }
    ))

    @evaluated
    def vconverter(self, *, make_signature):
        @parser.value_converter
        def converter(value):
            raise NotImplementedError
        sig = make_signature('*, par: conv', globals={'conv': converter})
        return (sig, parser.OptionParameter, '--par=CONVERTER', {
            'conv': converter,
            })

    @evaluated
    def default_type(self, *, make_signature):
        @parser.value_converter
        class FancyDefault(object):
            def __init__(self, arg):
                self.arg = arg
        deft = FancyDefault('ham')
        sig = make_signature('*, par=default', globals={'default': deft})
        return (sig, parser.OptionParameter, '[--par=FANCYDEFAULT]', {
            'conv': FancyDefault,
            'default': deft,
        })

    @evaluated
    def bad_default_good_conv(self, *, make_signature):
        class UnknownDefault(object):
            pass
        deft = UnknownDefault()
        sig = make_signature('*, par:str=default', globals={'default': deft})
        return (sig, parser.OptionParameter, '[--par=STR]', {
            'conv': parser.identity,
            'default': deft,
        })

    @evaluated
    def method_conv(self, *, make_signature):
        class Spam(object):
            def method(self, arg):
                return self
        s = Spam()
        conv = parser.value_converter(s.method, name='TCONV')
        sig = make_signature('*, par: conv', globals={'conv': conv})

        csig = parser.CliSignature.from_signature(sig)
        ba = self.read_arguments(csig, ['--par=arg'])
        arg = ba.kwargs['par']
        self.assertIs(arg, s)

        return (sig, parser.OptionParameter, '--par=TCONV', {
            'conv': conv
        })

    @evaluated
    def flagp_conv_long(self, *, make_signature):
        @parser.value_converter
        def conv(arg):
            return arg
        param = parser.FlagParameter(
            argument_name='par',
            value='eggs', conv=conv,
            aliases=['--par']
            )
        self.assertEqual(param.get_all_names(), '--par[=CONV]')
        sig = make_signature('*, par: p, o=False', globals={'p': param})

        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(self.read_arguments(csig, []).kwargs, {})
        self.assertEqual(self.read_arguments(csig, ['--par']).kwargs,
                         {'par': 'eggs'})
        self.assertEqual(self.read_arguments(csig, ['--par=ham']).kwargs,
                         {'par': 'ham'})

        return (sig, parser.FlagParameter, '[--par[=CONV]]', {
            'conv': conv,
        })

    @evaluated
    def flagp_conv_short(self, *, make_signature):
        @parser.value_converter
        def conv(arg):
            raise NotImplementedError
        param = parser.FlagParameter(
            argument_name='par',
            value='eggs', conv=conv,
            aliases=['--par', '-p']
            )
        self.assertEqual(param.get_all_names(), '-p, --par[=CONV]')
        sig = make_signature('*, par: p, o=False', globals={'p': param})

        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(self.read_arguments(csig, []).kwargs, {})
        self.assertEqual(self.read_arguments(csig, ['-p']).kwargs,
                         {'par': 'eggs'})
        self.assertEqual(self.read_arguments(csig, ['-po']).kwargs,
                         {'par': 'eggs', 'o': True})

        return (sig, parser.FlagParameter, '[-p]', {
            'conv': conv,
        })

    def test__alias_multi(self):
        sig = support.s('*, one: a', globals={'a': ('a', 'b', 'abc')})
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        self.assertEqual(type(cparam), parser.OptionParameter)
        self.assertEqual(str(cparam), '-a STR')
        self.assertEqual(cparam.display_name, '--one')
        self.assertEqual(cparam.aliases, ['--one', '-a', '-b', '--abc'])

    def test_param_inst(self):
        param = parser.Parameter('abc')
        sig = support.s('xyz: p', globals={'p': param})
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
            support.s('o: c', globals={'c': converter}),
            support.s('*, o: a', globals={'a': ("abc", converter)})
            ]
        for sig in sigs:
            sparam = list(sig.parameters.values())[0]
            self.assertRaises(CustExc, parser.CliSignature.convert_parameter, sparam)

    def test_parameterflag_repr(self):
        f1 = parser.ParameterFlag('someflag')
        self.assertEqual(repr(f1), 'clize.Parameter.someflag')
        f2 = parser.ParameterFlag('someflag', 'someobject')
        self.assertEqual(repr(f2), 'someobject.someflag')

    def test_clize_annotation_repr(self):
        skip_unless_typings_has_annotations(self)
        ann = Clize[int, 'a']
        self.assertEqual(repr(ann), f"clize.Clize[{int!r}, {'a'!r}]")

    def test_missing_type_annotation_param_warning(self):
        @parser.parameter_converter
        def converter_for_test(param, annotations, arg=0):
            return parser.default_converter(param, annotations, type_annotation=inspect.Parameter.empty)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            par = parser.parameter_converter(functools.partial(converter_for_test, arg=0))

        class MyConverterClass:
            __module__ = None
            def __call__(self, param, annotations):
                return parser.Parameter.IGNORE
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            inst = parser.parameter_converter(MyConverterClass())

        sigs = [
            support.s("one: ann", globals={"ann": converter_for_test}),
            support.s("one: ann", globals={"ann": par}),
            support.s("one: ann", globals={"ann": inst}),
        ]
        for sig in sigs:
            param = list(sig.parameters.values())[0]
            with self.assertWarns(DeprecationWarning):
                parser.CliSignature.convert_parameter(param)


class ParamHelpTests(SignatureFixtures):
    def _test(self, sig, expected, *, make_signature, desc="ds"):
        param = list(sig.parameters.values())[0]
        cparam = parser.CliSignature.convert_parameter(param)
        f = util.Formatter()
        with f.columns(indent=2) as cols:
            actual = cparam.show_help(desc, (), util.Formatter(), cols)
        self.assertEqual(actual, expected)

    plain_param = s("param"), ("param", "ds")
    param_default = s("param = 4"), ("param", "ds (type: INT, default: 4)")
    param_cli_default = s("param: ann", ann=Parameter.cli_default('5')), ("param", "ds (default: 5)")
    param_cli_default_overrides_default = s("param: ann = '2'", ann=Parameter.cli_default('5')), ("param", "ds (default: 5)")
    param_cli_default_none = s("param: ann = '2'", ann=Parameter.cli_default(None, convert=False)), ("param", "ds")


@parser.value_converter()
def conv_not_default(arg):
    return f'converted:{arg}'


class SigTests(SignatureFixtures):
    def _test(self, sig, str_rep, args, posargs, kwargs, *, make_signature, conversion_warning=None, parsing_warning=None):
        with self.maybe_expect_warning(conversion_warning):
            csig = parser.CliSignature.from_signature(sig)
        with self.maybe_expect_warning(parsing_warning):
            ba = self.read_arguments(csig, args)
        self.assertEqual(str(csig), str_rep)
        self.assertEqual(ba.args, posargs)
        self.assertEqual(ba.kwargs, kwargs)
        repr(ba) # ensure attrs repr doesn't crash

    no_param = s(''), '', (), [], {}

    pos = (
        s('one, two, three'), 'one two three',
        ('1', '2', '3'), ['1', '2', '3'], {})

    pos_empty = (
        s('one'), 'one',
        ('',), [''], {}
        )

    _two_str_usage = '--one=STR --two=STR'
    kw_glued = (
        s('*, one, two'), _two_str_usage,
        ('--one=1', '--two=2'), [], {'one': '1', 'two': '2'})
    kw_nonglued = (
        s('*, one, two'), _two_str_usage,
        ('--one', '1', '--two', '2'), [], {'one': '1', 'two': '2'})

    _two_str_a_usage = '-a STR -b STR'
    kw_short_nonglued = (
        s('*, one: "a", two: "b"'), _two_str_a_usage,
        ('-a', '1', '-b', '2'), [], {'one': '1', 'two': '2'})
    kw_short_glued = (
        s('*, one: "a", two: "b"'), _two_str_a_usage,
        ('-a1', '-b2'), [], {'one': '1', 'two': '2'})
    kw_short_case = (
        s('*, one: "a", two: "A"'), '-a STR -A STR',
        ('-a', 'one', '-A', 'two'), [], {'one': 'one', 'two': 'two'})

    pos_and_kw = (
        s('one, *, two, three, four: "a", five: "b"'),
        '--two=STR --three=STR -a STR -b STR one',
        ('1', '--two', '2', '--three=3', '-a', '4', '-b5'),
        ['1'], {'two': '2', 'three': '3', 'four': '4', 'five': '5'})
    pos_and_kw_mixed = (
        s('one, two, *, three'), '--three=STR one two',
        ('1', '--three', '3', '2'), ['1', '2'], {'three': '3'}
        )

    flag = s('*, one=False'), '[--one]', ('--one',), [], {'one': True}
    flag_absent = s('*, one=False'), '[--one]', (), [], {}
    flag_glued = (
        s('*, a=False, b=False, c=False'), '[-a] [-b] [-c]',
        ('-ac',), [], {'a': True, 'c': True}
        )

    _one_flag = s('*, one:"a"=False')
    _one_flag_u = '[-a]'
    flag_false = _one_flag, _one_flag_u, ('--one=',), [], {'one': False}
    flag_false_0 = _one_flag, _one_flag_u, ('--one=0',), [], {'one': False}
    flag_false_n = _one_flag, _one_flag_u, ('--one=no',), [], {'one': False}
    flag_false_f = _one_flag, _one_flag_u, ('--one=false',), [], {'one': False}

    collect_pos = s('*args'), '[args...]', ('1', '2', '3'), ['1', '2', '3'], {}
    pos_and_collect = (
        s('a, *args'), 'a [args...]',
        ('1', '2', '3'), ['1', '2', '3'], {})
    collect_and_kw = (
        s('*args, one'), '--one=STR [args...]',
        ('2', '--one', '1', '3'), ['2', '3'], {'one': '1'})

    conv = s('a=1'), '[a]', ('1',), [1], {}

    named_int_glued = (
        s('*, one:"a"=1, two:"b"="s"'), '[-a INT] [-b STR]',
        ('-a15bham',), [], {'one': 15, 'two': 'ham'})
    named_int_glued_negative = (
        s('*, one:"a"=1, two:"b"="s"'), '[-a INT] [-b STR]',
        ('-a-23bham',), [], {'one': -23, 'two': 'ham'})
    named_int_last = (
        s('*, one:"a"=1'), '[-a INT]',
        ('-a23',), [], {'one': 23})

    double_dash = (
        s('one, two, three'), 'one two three',
        ('first', '--', '--second', 'third'),
        ['first', '--second', 'third'], {}
        )

    pos_last_option = (
        s('one, two:P.L, *r, three'), '--three=STR one two [r...]',
        ('1', '--three=3', '2', '--four', '4'),
        ['1', '2', '--four', '4'], {'three': '3'}
        )
    kw_last_option = (
        s('one, two, *r, three:P.L'), '--three=STR one two [r...]',
        ('1', '--three=3', '2', '--four', '4'),
        ['1', '2', '--four', '4'], {'three': '3'}
        )

    ignored = s('one:P.I'), '', (), [], {}

    bytes = s("a: bytes"), 'a', ('\u1234',), [os.fsencode('\u1234')], {}
    bytes_named = s("*, a: bytes"), '-a BYTES', ('-a\u1234',), [], {'a': os.fsencode('\u1234')}

    path = s("*, a: ann", ann=pathlib.Path), '-a PATH', ('-a./abc/def',), [], {'a': pathlib.Path('./abc/def')}
    path_default = (
        s("*, a = default", default=pathlib.Path('./abc',)),
        '[-a PATH]', ('-a./def',), [], {'a': pathlib.Path('./def')},
    )

    def test_converter_ignore(self):
        @parser.parameter_converter
        def conv(param, annotations, *, type_annotation):
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

    def test_posparam_set_value_after_cli_default(self):
        param = parser.PositionalParameter(argument_name='two', display_name='two', default="two")
        sig = support.s('one: ann1 = "src_default", two:ann2="two"', globals={'ann1': Parameter.cli_default("one"), 'ann2': param})
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

    @evaluated
    def vconverter_keep_default(self, *, make_signature):
        @parser.value_converter
        def conv(arg):
            return 'converted'
        sig = make_signature('*, par:conv="default"', globals={'conv': conv})
        return (sig, '[--par=CONV]', (), [], {})

    @evaluated
    def vconverter_convert_value_equals(self, *, make_signature):
        with self.assertWarns(DeprecationWarning):
            @parser.value_converter(convert_default=True)
            def conv(arg):
                return 'c{}c'.format(arg)
        sig = make_signature('*, par:conv="default"', globals={'conv': conv})
        return (sig, '[--par=CONV]', ('--par=A',), [], {'par': 'cAc'}, options(conversion_warning=DeprecationWarning))

    @evaluated
    def vconverter_convert_value_spaced(self, *, make_signature):
        with self.assertWarns(DeprecationWarning):
            @parser.value_converter(convert_default=True)
            def conv(arg):
                return 'c{}c'.format(arg)
        sig = make_signature('*, par:conv="default"', globals={'conv': conv})
        return (sig, '[--par=CONV]', ('--par', 'A',), [], {'par': 'cAc'}, options(conversion_warning=DeprecationWarning))

    @evaluated
    def vconverter_convert_default(self, *, make_signature):
        with self.assertWarns(DeprecationWarning):
            @parser.value_converter(convert_default=True)
            def conv(arg):
                return 'converted'
        sig = make_signature('*, par:conv="default"', globals={'conv': conv})
        return (sig, '[--par=CONV]', (), [], {'par': 'converted'}, options(conversion_warning=DeprecationWarning))

    @evaluated
    def vconverter_convert_default_after_pos(self, *, make_signature):
        with self.assertWarns(DeprecationWarning):
            @parser.value_converter(convert_default=True)
            def conv(arg):
                return 'converted'
        sig = make_signature('first="otherdefault", par:conv="default"', globals={'conv': conv})
        return (sig, '[first] [par]', (), ['otherdefault', 'converted'], {}, options(conversion_warning=DeprecationWarning))

    cli_default_no_src_default = (s(
        'par: ann',
        ann=(conv_not_default, Parameter.cli_default("cli_default"))
    ), "[par]", (), ["converted:cli_default"], {})

    cli_default_src_default = (s(
        'par: ann = "default"',
        ann=(conv_not_default, Parameter.cli_default("cli_default"))
    ), "[par]", (), ["converted:cli_default"], {})

    cli_default_dont_convert = (s(
        'par: ann = "default"',
        ann=(conv_not_default, Parameter.cli_default("cli_default", convert=False))
    ), "[par]", (), ["cli_default"], {})

    cli_default_none = (s(
        'par: ann = "default"',
        ann=(conv_not_default, Parameter.cli_default(None, convert=False))
    ), "[par]", (), [None], {})

    cli_default_after_pos = (s(
        'first="otherdefault", par:conv="src_default"', conv=Parameter.cli_default("default")
    ), "[first] [par]", (), ["otherdefault", "default"], {})

    cli_default_for_default_converter = (s(
        'par: ann',
        ann=(int, Parameter.cli_default("1234")),
    ), "[par]", (), [1234], {})


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


class UnknownAnnotation(object):
    pass


class UnknownDefault(object):
    def __init__(self, arg):
        self.arg = arg


class BadParamTests(SignatureFixtures):
    def _test(self, sig, exp_msg, *, raises=ValueError, make_signature):
        params = list(sig.parameters.values())
        with self.assertRaises(raises) as ar:
            parser.CliSignature.convert_parameter(params[0])
        if exp_msg is not None:
            self.assertEqual(exp_msg, str(ar.exception))

    alias_superfluous = s('one: "a"'), "Cannot give aliases for a positional parameter."
    alias_spaces = s('*, one: "a b"'), "Cannot have whitespace in aliases."
    alias_duplicate = s('*, one: dup', dup=('a', 'a')), "Duplicate alias 'a'"
    _ua = UnknownAnnotation()
    unknown_annotation = (
        s('one: ua', ua=_ua), f"Unknown annotation {_ua!r}\n"
        "If you intended for it to be a value or parameter converter, "
        "make sure the appropriate decorator was applied.")
    def _uc(arg):
        raise NotImplementedError
    unknown_callable = (
        s('one: uc', uc=_uc), f"Unknown annotation {_uc!r}\n"
        "If you intended for it to be a value or parameter converter, "
        "make sure the appropriate decorator was applied.")
    unknown_typing = skip_unless_typings_has_annotations, defer(lambda: (
        s("*, one: ann", ann=typing.Annotated[UnknownDefault, Clize['a']]),
        f"Cannot find a value converter for type {UnknownDefault!r}. "
        "Please specify one as an annotation.\n"
        "If the type should be used to convert the value, "
        "make sure it is decorated with clize.parser.value_converter()"
    ))
    _ud = UnknownDefault('stuff')
    bad_custom_default = (
        s('one=bd', bd=_ud),
        f"Cannot find value converter for default value {_ud!r}. "
        "Please specify one as an annotation.\n"
        "If the default value's type should be used to convert the value, "
        "make sure it is decorated with clize.parser.value_converter()")
    coerce_twice = s('one: co', co=(str, int)), "Value converter specified twice in annotation: str int"
    dup_pconverter = (
        s('one: a', a=(parser.default_converter, parser.default_converter)),
        "Parameter converter 'default_converter' must be the first "
        "element of a parameter's annotation")
    unimplemented_parameter = (
        s('**kwargs'),
        "This converter cannot convert parameter 'kwargs' to a CLI parameter")

    @parser.use_mixin
    class _type_error_converter(parser.ParameterWithValue):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise TypeError("error for tests")
    type_error_not_due_to_missing_type_annotation_param = (
        s('one: ann', ann=_type_error_converter),
        repeated_test.options(raises=TypeError),
        "error for tests",
    )


class BadSigTests(Fixtures):
    def _test(self, sig_str):
        sig = support.s(sig_str, pre='from clize import Parameter')
        self.assertRaises(ValueError, parser.CliSignature.from_signature, sig)

    alias_overlapping = '*, one: "a", two: "a"',
