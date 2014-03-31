# clize -- A command-line argument parser for Python
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

"""
interpret function signatures and read commandline arguments
"""

import itertools

import six

from clize import errors, util

funcsigs = util.funcsigs


class ParameterFlag(object):
    def __init__(self, name, prefix='clize.Parameter'):
        self.name = name
        self.prefix = prefix

    def __repr__(self):
        return '{0.prefix}.{0.name}'.format(self)


class Parameter(object):
    """Represents a python parameter/CLI parameter pair."""
    E = EAT_REST = ParameterFlag('EAT_REST')
    R = REQUIRED = ParameterFlag('REQUIRED')
    L = LAST_OPTION = ParameterFlag('LAST_OPTION')
    # I = IGNORE = ParameterFlag('IGNORE')
    U = UNDOCUMENTED = ParameterFlag('UNDOCUMENTED')
    # M = MULTIPLE = ParameterFlag('MULTIPLE')

    required = False

    def __init__(self, display_name, undocumented=False, last_option=None):
        self.display_name = display_name
        self.undocumented = undocumented
        self.last_option = last_option

    @classmethod
    def from_parameter(self, param):
        if param.annotation != param.empty:
            annotations = util.maybe_iter(param.annotation)
        else:
            annotations = []

        named = param.kind in (param.KEYWORD_ONLY, param.VAR_KEYWORD)
        aliases = [param.name]
        default = util.UNSET
        typ = util.identity

        kwargs = {
            'argument_name': param.name,
            'undocumented': Parameter.UNDOCUMENTED in annotations,
            }

        if param.default is not param.empty:
            if Parameter.REQUIRED not in annotations:
                default = param.default
            if default is not None:
                typ = type(param.default)

        if Parameter.LAST_OPTION in annotations:
            kwargs['last_option'] = True

        set_coerce = False
        for thing in annotations:
            if isinstance(thing, Parameter):
                return thing
            elif callable(thing):
                if set_coerce:
                    raise ValueError(
                        "Coercion function specified twice in annotation: "
                        "{0.__name__} {1.__name__}".format(typ, thing))
                typ = thing
                set_coerce = True
            elif isinstance(thing, six.string_types):
                if not named:
                    raise ValueError("Cannot give aliases for a positional "
                                     "parameter.")
                if len(thing.split()) > 1:
                    raise ValueError("Cannot have whitespace in aliases.")
                aliases.append(thing)
            elif isinstance(thing, ParameterFlag):
                pass
            else:
                raise ValueError(thing)

        if named:
            kwargs['aliases'] = [
                util.name_py2cli(alias, named)
                for alias in aliases]
            if default is False and typ is bool:
                return FlagParameter(value=True, false_value=False, **kwargs)
            else:
                kwargs['default'] = default
                kwargs['typ'] = typ
                if typ is int:
                    return IntOptionParameter(**kwargs)
                else:
                    return OptionParameter(**kwargs)
        else:
            kwargs['display_name'] = util.name_py2cli(param.name)
            if param.kind == param.VAR_POSITIONAL:
                return ExtraPosArgsParameter(
                    required=Parameter.REQUIRED in annotations,
                    typ=typ, **kwargs)
            else:
                return PositionalParameter(default=default, typ=typ, **kwargs)

    def read_argument(self, ba, i):
        raise NotImplementedError

    def apply_generic_flags(self, ba):
        if self.last_option:
            ba.posarg_only = True

    def format_type(self):
        return ''

    @util.property_once
    def full_name(self):
        return self.display_name + self.format_type()

    def __str__(self):
        return self.display_name


class ParameterWithSourceEquivalent(Parameter):
    def __init__(self, argument_name, **kwargs):
        super(ParameterWithSourceEquivalent, self).__init__(**kwargs)
        self.argument_name = argument_name


class PositionalBindingParameter(Parameter):
    pass


class KeywordBindingParameter(Parameter):
    pass


class ParameterWithValue(Parameter):
    def __init__(self, typ=util.identity, default=util.UNSET, **kwargs):
        super(ParameterWithValue, self).__init__(**kwargs)
        self.typ = typ
        self.default = default

    @property
    def required(self):
        return self.default is util.UNSET

    def coerce_value(self, arg):
        try:
            return self.typ(arg)
        except ValueError as e:
            exc = errors.BadArgumentFormat(self.typ, arg)
            exc.__cause__ = e
            raise exc

    def format_type(self):
        if (
                self.typ is not util.identity
                and not issubclass(self.typ, six.string_types)
            ):
            return '=' + util.name_type2cli(self.typ)
        return ''

    @util.property_once
    def full_name(self):
        return self.display_name + self.format_type()

    def __str__(self):
        if self.required:
            return self.full_name
        else:
            return '[{0}]'.format(self.full_name)


class PositionalParameter(ParameterWithValue, ParameterWithSourceEquivalent,
                          PositionalBindingParameter):
    def read_argument(self, ba, i):
        val = self.coerce_value(ba.in_args[i])
        ba.args.append(val)


class NamedParameter(Parameter):
    def __init__(self, aliases, **kwargs):
        kwargs.setdefault('display_name', aliases[0])
        super(NamedParameter, self).__init__(**kwargs)
        self.aliases = aliases

    __key_count = itertools.count()
    @classmethod
    def alias_key(cls, name):
        return len(name) - len(name.lstrip('-')), next(cls.__key_count)

    @util.property_once
    def full_name(self):
        return ', '.join(sorted(self.aliases, key=self.alias_key)
            ) + self.format_type()

    def __str__(self):
        return '[{0}]'.format(self.display_name)

    def redispatch_short_arg(self, rest, ba, i):
        if not rest:
            return
        try:
            nparam = ba.sig.aliases['-' + rest[0]]
        except KeyError as e:
            raise errors.UnknownOption(e.args[0])
        orig_args = ba.in_args
        ba.in_args = ba.in_args[:i] + ('-' + rest,) + ba.in_args[i + 1:]
        try:
            nparam.read_argument(ba, i)
        finally:
            ba.in_args = orig_args
        ba.unsatisfied.discard(nparam)


class FlagParameter(NamedParameter, ParameterWithSourceEquivalent,
                    KeywordBindingParameter):
    def __init__(self, value, false_value, **kwargs):
        super(FlagParameter, self).__init__(**kwargs)
        self.value = value
        self.false_value = false_value

    def read_argument(self, ba, i):
        arg = ba.in_args[i]
        if arg[1] == '-':
            ba.kwargs[self.argument_name] = (
                self.value if self.is_flag_activation(arg)
                else self.false_value
                )
        else:
            ba.kwargs[self.argument_name] = self.value
            self.redispatch_short_arg(arg[2:], ba, i)


    def is_flag_activation(self, arg):
        if arg[1] != '-':
            return True
        arg, sep, val = arg.partition('=')
        return (
            not sep or
            val and val.lower() not in ('0', 'n', 'no', 'f', 'false')
            )

    def format_type(self):
        return ''


class OptionParameter(NamedParameter, ParameterWithValue,
                      ParameterWithSourceEquivalent, KeywordBindingParameter):
    def read_argument(self, ba, i):
        if self.argument_name in ba.kwargs:
            raise errors.DuplicateNamedArgument()
        arg = ba.in_args[i]
        if arg.startswith('--'):
            name, glued, val = arg.partition('=')
        else:
            arg = arg.lstrip('-')
            if len(arg) > 1:
                glued = True
                val = arg[1:]
            else:
                glued = False
        if not glued:
            try:
                val = ba.in_args[i+1]
            except IndexError:
                raise errors.MissingValue
        ba.kwargs[self.argument_name] = self.coerce_value(val)
        ba.skip = not glued

    def format_type(self):
        return '=' + util.name_type2cli(self.typ)

    def __str__(self):
        if self.required:
            fmt = '{0}{1}'
        else:
            fmt = '[{0}{1}]'
        return fmt.format(self.display_name, self.format_type())

def split_int_rest(s):
    for i, c, in enumerate(s):
        if not c.isdigit():
            return s[:i], s[i:]

class IntOptionParameter(OptionParameter):
    def read_argument(self, ba, i):
        if self.argument_name in ba.kwargs:
            raise errors.DuplicateNamedArgument()
        arg = ba.in_args[i]
        if arg.startswith('--'):
            super(IntOptionParameter, self).read_argument(ba, i)
            return

        arg = arg.lstrip('-')[1:]
        if not arg:
            super(IntOptionParameter, self).read_argument(ba, i)
            return

        val, rest = split_int_rest(arg)
        ba.kwargs[self.argument_name] = self.coerce_value(val)

        self.redispatch_short_arg(rest, ba, i)


class MultiParameter(ParameterWithValue):
    def __str__(self):
        return '[{0}...]'.format(self.name)

    def get_collection(self, ba):
        raise NotImplementedError

    def read_argument(self, ba, i):
        val = self.coerce_value(ba.in_args[i])
        self.get_collection(ba).append(val)
        return 0, None, None, None


class MultiOptionParameter(NamedParameter, MultiParameter):
    required = False

    def get_collection(self, ba):
        return ba.kwargs.setdefault(self.argument_name, [])


class EatAllPositionalParameter(MultiParameter):
    def get_collection(self, ba):
        return ba.args


class EatAllOptionParameterArguments(EatAllPositionalParameter):
    def __init__(self, param, **kwargs):
        super(EatAllOptionParameterArguments, self).__init__(
            display_name='...', undocumented=False, **kwargs)
        self.param = param

    def read_argument(self, ba, i):
        super(EatAllOptionParameterArguments, self).read_argument(ba, i)


class IgnoreAllOptionParameterArguments(EatAllOptionParameterArguments):
    def read_argument(self, ba, i):
        pass


class EatAllOptionParameter(MultiOptionParameter):
    extra_type = EatAllOptionParameterArguments

    def __init__(self, **kwargs):
        super(EatAllOptionParameter, self).__init__(**kwargs)
        self.args_param = self.extra_type(self)

    def read_argument(self, ba, i):
        super(EatAllOptionParameter, self).read_argument(ba, i)
        ba.post_name.append(ba.in_args[i])
        ba.posarg_only = True
        ba.sticky = self.args_param


class FallbackCommandParameter(EatAllOptionParameter):
    def __init__(self, func, **kwargs):
        super(FallbackCommandParameter, self).__init__(**kwargs)
        self.func = func
        self.ignore_all = IgnoreAllOptionParameterArguments(self)

    @util.property_once
    def description(self):
        try:
            return self.func.helper.description
        except AttributeError:
            pass

    def get_collection(self, ba):
        return []

    def read_argument(self, ba, i):
        ba.args[:] = []
        ba.kwargs.clear()
        super(FallbackCommandParameter, self).read_argument(ba, i)
        ba.func = self.func
        if i:
            ba.sticky = self.ignore_all


class AlternateCommandParameter(FallbackCommandParameter):
    def read_argument(self, ba, i):
        if i:
            raise errors.ArgsBeforeAlternateCommand(self)
        return super(AlternateCommandParameter, self).read_argument(ba, i)


class ExtraPosArgsParameter(PositionalParameter):
    required = None # clear required property from ParameterWithValue

    def __init__(self, required=False, **kwargs):
        super(ExtraPosArgsParameter, self).__init__(**kwargs)
        self.required = required

    def read_argument(self, ba, i):
        super(ExtraPosArgsParameter, self).read_argument(ba, i)
        ba.sticky = self

    def __str__(self):
        if self.required:
            fmt = '{0}...'
        else:
            fmt = '[{0}...]'
        return fmt.format(self.display_name)


class CliSignature(object):
    param_cls = Parameter

    def __init__(self, parameters):
        pos = self.positional = []
        named = self.named = []
        alt = self.alternate = []
        aliases = self.aliases = {}
        required = self.required = set()
        for param in parameters:
            required_ = getattr(param, 'required', False)
            func = getattr(param, 'func', None)
            aliases_ = getattr(param, 'aliases', None)

            if required_:
                required.add(param)

            if aliases_ is not None:
                for alias in aliases_:
                    aliases[alias] = param

            if func:
                alt.append(param)
            elif aliases_ is not None:
                named.append(param)
            else:
                pos.append(param)

    @classmethod
    def from_signature(cls, sig, extra=()):
        return cls(
            itertools.chain(
                (
                    cls.param_cls.from_parameter(param)
                    for param in sig.parameters.values()
                ), extra))

    def read_arguments(self, args, name='unnamed'):
        return CliBoundArguments(self, args, name)

    def __str__(self):
        return ' '.join(
            str(p)
            for p in itertools.chain(self.named, self.positional)
            if not p.undocumented
            )


class SeekFallbackCommand(object):
    def __enter__(self):
        pass

    def __exit__(self, typ, exc, tb):
        if exc is None:
            return
        try:
            pos = exc.pos
            ba = exc.ba
        except AttributeError:
            return

        for i, arg in enumerate(ba.in_args[pos + 1:], pos +1):
            param = ba.sig.aliases.get(arg, None)
            if param in ba.sig.alternate:
                try:
                    param.read_argument(ba, i)
                except errors.ArgumentError:
                    continue
                ba.unsatisfied.clear()
                return True


class CliBoundArguments(object):
    def __init__(self, sig, args, name):
        self.sig = sig
        self.name = name
        self.in_args = args
        self._read_arguments()

    def _read_arguments(self):
        self.func = None
        self.post_name = []
        self.args = []
        self.kwargs = {}

        self.sticky = None
        self.posarg_only = False
        self.skip = 0
        self.unsatisfied = set(self.sig.required)

        posparam = iter(self.sig.positional)

        with SeekFallbackCommand():
            for i, arg in enumerate(self.in_args):
                if self.skip > 0:
                    self.skip -= 1
                    continue
                with errors.SetArgumentErrorContext(pos=i, val=arg, ba=self):
                    if self.posarg_only or arg[0] != '-' or len(arg) < 2:
                        if self.sticky is not None:
                            param = self.sticky
                        else:
                            try:
                                param = next(posparam)
                            except StopIteration:
                                exc = errors.TooManyArguments(self.in_args[i:])
                                exc.__cause__ = None
                                raise exc
                    elif arg == '--':
                        self.posarg_only = True
                        continue
                    else:
                        if arg.startswith('--'):
                            name = arg.partition('=')[0]
                        else:
                            name = arg[:2]
                        try:
                            param = self.sig.aliases[name]
                        except KeyError:
                            raise errors.UnknownOption(name)
                    with errors.SetArgumentErrorContext(param=param):
                        param.read_argument(self, i)
                        self.unsatisfied.discard(param)
                        param.apply_generic_flags(self)

        if self.unsatisfied and not self.func:
            raise errors.MissingRequiredArguments(self.unsatisfied)

        del self.sticky, self.posarg_only, self.skip, self.unsatisfied

    def __iter__(self):
        yield self.func
        yield self.post_name
        yield self.args
        yield self.kwargs
