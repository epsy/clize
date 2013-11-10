# clize - automatically generate command-line interfaces from callables
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

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
                raise TypeError(thing)

        if named:
            kwargs['aliases'] = [
                util.name_py2cli(alias, named)
                for alias in aliases]
            if default is False and typ is bool:
                return FlagParameter(value=True, **kwargs)
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

    def read_one_argument(self, arg, ba):
        raise NotImplementedError

    def read_argument(self, args, i, ba):
        self.read_one_argument(args[i], ba)
        return 0, None, self.last_option, None

    def finalize(self, ba):
        pass

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
        if self.typ is not util.identity and self.typ not in six.string_types:
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
    def read_one_argument(self, arg, ba):
        val = self.coerce_value(arg)
        ba.args.append(val)


class NamedParameter(Parameter):
    def __init__(self, aliases, **kwargs):
        if aliases:
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


class FlagParameter(NamedParameter, ParameterWithSourceEquivalent,
                    KeywordBindingParameter):
    def __init__(self, value, **kwargs):
        super(FlagParameter, self).__init__(**kwargs)
        self.value = value

    def read_one_argument(self, arg, ba):
        ba.kwargs[self.argument_name] = self.value

    def format_type(self):
        return ''


class OptionParameter(NamedParameter, ParameterWithValue,
                      ParameterWithSourceEquivalent, KeywordBindingParameter):
    def read_argument(self, args, i, ba):
        if self.argument_name in ba.kwargs:
            raise errors.DuplicateNamedArgument()
        arg = args[i]
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
                val = args[i+1]
            except IndexError:
                raise errors.MissingValue
        ba.kwargs[self.argument_name] = self.coerce_value(val)
        return int(not glued), None, None, None

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
    def read_argument(self, args, i, ba):
        if self.argument_name in ba.kwargs:
            raise errors.DuplicateNamedArgument()
        arg = args[i]
        if arg.startswith('--'):
            return super().read_argument(args, i, ba)

        arg = arg.lstrip('-')[1:]
        if not arg:
            return super().read_argument(args, i, ba)

        val, rest = split_int_rest(arg)
        ba.kwargs[self.argument_name] = self.coerce_value(val)

        if not rest:
            return 0, None, None, None

        nparam = ba.sig.aliases['-' + rest[0]]
        fake_args = args[:i] + ('-' + rest,) + args[i + 1:]
        ret = nparam.read_argument(fake_args, i, ba)
        ba.unsatisfied.discard(nparam)
        return ret


class MultiParameter(ParameterWithValue):
    def __str__(self):
        return '[{0}...]'.format(self.name)

    def get_collection(self, ba):
        raise NotImplementedError

    def read_argument(self, args, i, ba):
        val = self.coerce_value(args[i])
        self.get_collection(ba).append(val)
        return 0, None, None, None


class MultiOptionParameter(NamedParameter, MultiParameter):
    required = False

    def get_collection(self, ba):
        return ba.kwargs.setdefault(self.argument_name, [])


class EatAllPositionalParameter(MultiParameter):
    def get_collection(self, ba):
        return ba.args


class EatAllOptionParameter(MultiOptionParameter):
    def __init__(self, **kwargs):
        super(EatAllOptionParameter, self).__init__(**kwargs)
        self.args = EatAllOptionParameterArguments(self)

    @property
    def sticky(self):
        return self

    def read_argument(self, args, i, ba):
        skip, _, _, func = super(EatAllOptionParameter, self).read_argument(
            args, i, ba)
        ba.post_name.append(args[i])
        return skip, self.args, True, func


class EatAllOptionParameterArguments(EatAllPositionalParameter):
    def __init__(self, param, **kwargs):
        super(EatAllOptionParameterArguments, self).__init__(
            display_name='...', undocumented=False, **kwargs)
        self.param = param

    def read_argument(self, args, i, ba):
        skip, _, posarg_only, _ = super(
            EatAllOptionParameterArguments, self).read_argument(args, i, ba)
        return skip, self, posarg_only, getattr(self.param, 'func', None)


class FallbackCommandParameter(EatAllOptionParameter):
    def __init__(self, func, **kwargs):
        super(FallbackCommandParameter, self).__init__(**kwargs)
        self.func = func

    @util.property_once
    def description(self):
        try:
            return self.func.helper.description
        except AttributeError:
            pass

    def get_collection(self, ba):
        return []

    def read_argument(self, args, i, ba):
        skip, sticky, posarg_only, _ = super(
            FallbackCommandParameter, self).read_argument(args, i, ba)
        return skip, None if i else sticky, posarg_only, self.func


class AlternateCommandParameter(FallbackCommandParameter):
    def read_argument(self, args, i, ba):
        if i:
            raise errors.ArgsBeforeAlternateCommand(self)
        return super(AlternateCommandParameter, self).read_argument(
            args, i, ba)


class ExtraPosArgsParameter(PositionalParameter):
    required = None # clear required property from ParameterWithValue

    def __init__(self, required=False, **kwargs):
        super(ExtraPosArgsParameter, self).__init__(**kwargs)
        self.required = required

    def read_argument(self, args, i, ba):
        skip, _, posarg_only, func = super(
            ExtraPosArgsParameter, self).read_argument(args, i, ba)
        return skip, self, posarg_only, func

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

    def read_arguments(self, args):
        return CliBoundArguments(self, args)

    def __str__(self):
        return ' '.join(
            str(p)
            for p in itertools.chain(self.named, self.positional)
            if not p.undocumented
            )


class CliBoundArguments(object):
    def __init__(self, sig, args):
        self.sig = sig
        self.in_args = args
        self._read_arguments()

    def _read_arguments(self):
        self.func = None
        self.post_name = []
        self.args = []
        self.kwargs = {}

        posparam = iter(self.sig.positional)

        func = None
        sticky = None
        posarg_only = False
        skip = 0
        unsatisfied = self.unsatisfied = set(self.sig.required)

        for i, arg in enumerate(self.in_args):
            if skip > 0:
                skip -= 1
                continue
            with errors.SetArgumentErrorContext(pos=i, val=arg):
                if not posarg_only and arg == '--':
                    posarg_only = True
                    continue
                elif not posarg_only and arg.startswith('-') and len(arg) >= 2:
                    if arg.startswith('--'):
                        name = arg.partition('=')[0]
                    else:
                        name = arg[:2]
                    try:
                        param = self.sig.aliases[name]
                    except KeyError:
                        raise errors.UnknownOption(name)
                else:
                    if sticky:
                        param = sticky
                    else:
                        try:
                            param = next(posparam)
                        except StopIteration:
                            exc = errors.TooManyArguments(self.in_args[i:])
                            exc.__cause__ = None
                            raise exc
                with errors.SetArgumentErrorContext(param=param):
                    skip, sticky_, posarg_only_, func = param.read_argument(
                        self.in_args, i, self)
                    if sticky_ is not None:
                        sticky = sticky_
                    posarg_only = (posarg_only
                                   if posarg_only_ is None else posarg_only_)
                    unsatisfied.discard(param)

        if func:
            self.func = func
        elif unsatisfied:
            raise errors.MissingRequiredArguments(unsatisfied)

    def __iter__(self):
        yield self.func
        yield self.post_name
        yield self.args
        yield self.kwargs
