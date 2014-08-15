# clize -- A command-line argument parser for Python
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

"""
interpret function signatures and read commandline arguments
"""

import itertools

import six

from clize import errors, util


class ParameterFlag(object):
    def __init__(self, name, prefix='clize.Parameter'):
        self.name = name
        self.prefix = prefix

    def __repr__(self):
        return '{0.prefix}.{0.name}'.format(self)


def parameter_converter(obj):
    obj._clize__parameter_converter = True
    return obj


def default_converter(param, annotations):
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
            if thing in aliases:
                raise ValueError("Duplicate alias " + repr(thing))
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


class Parameter(object):
    """Represents a CLI parameter.

    :param str display_name: The 'default' representation of the parameter.
    :param bool undocumented:
        If true, hides the parameter from the command help.
    :param last_option: 
    """

    required = False
    converter = default_converter

    def __init__(self, display_name, undocumented=False, last_option=None):
        self.display_name = display_name
        self.undocumented = undocumented
        self.last_option = last_option

    @classmethod
    def from_parameter(self, param):
        """"""
        if param.annotation != param.empty:
            annotations = util.maybe_iter(param.annotation)
        else:
            annotations = []

        for i, annotation in enumerate(annotations):
            if getattr(annotation, '_clize__parameter_converter', False):
                conv = annotation
                annotations = annotations[:i] + annotations[i+1:]
                break
        else:
            conv = default_converter

        return conv(param, annotations)

    R = REQUIRED = ParameterFlag('REQUIRED')
    """Annotate a parameter with this to force it to be required.

    Mostly only useful for ``*args`` parameters. In other cases simply don't
    provide a default value."""

    L = LAST_OPTION = ParameterFlag('LAST_OPTION')
    """Annotate a parameter with this and all following arguments will be
    processed as positional."""

    # I = IGNORE = ParameterFlag('IGNORE')

    U = UNDOCUMENTED = ParameterFlag('UNDOCUMENTED')
    """Parameters annotated with this will be omitted from the
    documentation."""

    # M = MULTIPLE = ParameterFlag('MULTIPLE')

    def read_argument(self, ba, i):
        """Reads one or more arguments from ``ba.in_args`` from position ``i``.

        :param clize.parser.CliBoundArguments ba:
            The bound arguments object this call is expected to mutate.
        :param int i:
            The current position in ``ba.args``.
        """
        raise NotImplementedError

    def apply_generic_flags(self, ba):
        """Called after `read_argument` in order to set attributes on ``ba``
        independently of the arguments.

        :param clize.parser.CliBoundArguments ba:
            The bound arguments object this call is expected to mutate.
        """
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
    """Parameter that relates to a function parameter in the source.

    :param str argument_name: The name of the parameter.
    """
    def __init__(self, argument_name, **kwargs):
        super(ParameterWithSourceEquivalent, self).__init__(**kwargs)
        self.argument_name = argument_name


class ParameterWithValue(Parameter):
    """A parameter that stores a value, with possible default and/or
    conversion.

    :param callable typ: A callable to convert the value or raise `ValueError`.
        Defaults to `.util.identity`.
    :param default: A default value for the parameter or `.util.UNSET`.
    """

    def __init__(self, typ=util.identity, default=util.UNSET, **kwargs):
        super(ParameterWithValue, self).__init__(**kwargs)
        self.typ = typ
        self.default = default

    @property
    def required(self):
        """Tells if the parameter has no default value."""
        return self.default is util.UNSET

    def coerce_value(self, arg):
        """Coerces ``arg`` using the ``typ`` function. Raises
        `.errors.BadArgumentFormat` if the coercion function raises
        `ValueError`.
        """
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


class PositionalParameter(ParameterWithValue, ParameterWithSourceEquivalent):
    """Equivalent of a positional-only parameter in python."""
    def read_argument(self, ba, i):
        val = self.coerce_value(ba.in_args[i])
        ba.args.append(val)


class NamedParameter(Parameter):
    """Equivalent of a keyword-only parameter in python.

    :param aliases: The arguments that trigger this parameter. The first alias
        is used to refer to the parameter.
    :type aliases: sequence of strings
    """
    def __init__(self, aliases, **kwargs):
        kwargs.setdefault('display_name', aliases[0])
        super(NamedParameter, self).__init__(**kwargs)
        self.aliases = aliases

    __key_count = itertools.count()
    @classmethod
    def alias_key(cls, name):
        """Key function to sort aliases in source order, but with short
        forms(one dash) first."""
        return len(name) - len(name.lstrip('-')), next(cls.__key_count)

    @util.property_once
    def full_name(self):
        return ', '.join(sorted(self.aliases, key=self.alias_key)
            ) + self.format_type()

    def __str__(self):
        return '[{0}]'.format(self.display_name)

    def redispatch_short_arg(self, rest, ba, i):
        """Processes the rest of an argument as if it was a new one prefixed
        with one dash."""
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


class FlagParameter(NamedParameter, ParameterWithSourceEquivalent):
    """A named parameter that takes no argument.

    :param value: The value when the argument is present.
    :param false_value: The value when the argument is given one of the
        false value triggers using ``--param=xyz``.
    """

    false_triggers = '0', 'n', 'no', 'f', 'false'

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
        """Checks if an argument triggers the true or false value."""
        if arg[1] != '-':
            return True
        arg, sep, val = arg.partition('=')
        return (
            not sep or
            val and val.lower() not in self.false_triggers
            )

    def format_type(self):
        return ''


class OptionParameter(NamedParameter, ParameterWithValue,
                      ParameterWithSourceEquivalent):
    """A named parameter that takes an argument."""

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
    """A named parameter that takes an integer as argument. The short form
    of it can be chained with the short form of other named parameters."""

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
    """Parameter that can collect multiple values."""

    def __str__(self):
        return '[{0}...]'.format(self.name)

    def get_collection(self, ba):
        """Return an object that new values will be appended to."""
        raise NotImplementedError

    def read_argument(self, ba, i):
        val = self.coerce_value(ba.in_args[i])
        self.get_collection(ba).append(val)


class MultiOptionParameter(NamedParameter, MultiParameter):
    """Named parameter that can collect multiple values."""

    required = False

    def get_collection(self, ba):
        return ba.kwargs.setdefault(self.argument_name, [])


class EatAllPositionalParameter(MultiParameter):
    """Helper parameter that collects multiple values to be passed as
    positional arguments to the callee."""

    def get_collection(self, ba):
        return ba.args


class EatAllOptionParameterArguments(EatAllPositionalParameter):
    """Helper parameter for .EatAllOptionParameter that adds the remaining
    arguments as positional arguments for the function."""

    def __init__(self, param, **kwargs):
        super(EatAllOptionParameterArguments, self).__init__(
            display_name='...', undocumented=False, **kwargs)
        self.param = param


class IgnoreAllOptionParameterArguments(EatAllOptionParameterArguments):
    """Helper parameter for .EatAllOptionParameter that ignores the remaining
    arguments."""

    def read_argument(self, ba, i):
        pass


class EatAllOptionParameter(MultiOptionParameter):
    """Parameter that collects all remaining arguments as positional
    arguments, even those which look like named arguments."""

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
    """Parameter that sets an alternative function when triggered. When used
    as an argument other than the first all arguments are discarded."""

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
    """Parameter that sets an alternative function when triggered. When used
    as an argument other than the first all arguments are discarded."""

    def read_argument(self, ba, i):
        if i:
            raise errors.ArgsBeforeAlternateCommand(self)
        return super(AlternateCommandParameter, self).read_argument(ba, i)


class ExtraPosArgsParameter(PositionalParameter):
    """Parameter that forwards all remaining positional arguments to the
    callee."""

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
    """A collection of parameters that can be used to translate CLI arguments
    to function arguments.

    :param iterable parameters: The parameters to use.

    .. attribute:: positional

        List of positional parameters.

    .. attribute:: alternate

        List of parameters that initiate an alternate action.

    .. attribute:: named

        List of named parameters that aren't in `.alternate`.

    .. attribute:: aliases
        :annotation: = {}

        Maps parameter names to `Parameter` instances.

    .. attribute:: required
        :annotation: = set()

        A set of all required parameters.
    """

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
                    existing = aliases.get(alias)
                    if existing is not None:
                        raise ValueError(
                            "Parameters {0.display_name} and {1.display_name} "
                            "use a duplicate alias {2!r}."
                            .format(existing, param, alias)
                            )
                    aliases[alias] = param

            if func:
                alt.append(param)
            elif aliases_ is not None:
                named.append(param)
            else:
                pos.append(param)

    param_cls = Parameter
    """The parameter class `.from_signature` will use to convert source
    parameters to CLI parameters"""

    @classmethod
    def from_signature(cls, sig, extra=()):
        """Takes a signature object and returns an instance of this class
        derived from it.

        :param inspect.Signature sig: The signature object to use.
        :param iterable extra: Extra parameter instances to include.
        """
        return cls(
            itertools.chain(
                (
                    cls.param_cls.from_parameter(param)
                    for param in sig.parameters.values()
                ), extra))

    def read_arguments(self, args, name='unnamed'):
        """Returns a `.CliBoundArguments` instance for this CLI signature
        bound to the given arguments.

        :param sequence args: The CLI arguments, minus the script name.
        :param str name: The script name.
        """
        return CliBoundArguments(self, args, name)

    def __str__(self):
        return ' '.join(
            str(p)
            for p in itertools.chain(self.named, self.positional)
            if not p.undocumented
            )


class _SeekFallbackCommand(object):
    """Context manager that tries to seek a fallback command if an error was
    raised."""
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
    """Command line arguments bound to a `.CliSignature` instance.

    :param CliSignature sig: The signature to bind against.
    :param sequence args: The CLI arguments, minus the script name.
    :param str name: The script name.

    .. attribute:: sig

        The signature being bound to.

    .. attribute:: in_args

        The CLI arguments, minus the script name.

    .. attribute:: name

        The script name.

    .. attribute:: args
        :annotation: = []

        List of arguments to pass to the target function.

    .. attribute:: kwargs
        :annotation: = {}

        Mapping of named arguments to pass to the target function.

    .. attribute:: func
        :annotation: = None

        If not `None`, replaces the target function.

    .. attribute:: post_name
        :annotation: = []

        List of words to append to the script name when passed to the target
        function.

    The following attributes only exist while arguments are being processed:

    .. attribute:: sticky
       :annotation: = None

       If not `None`, a parameter that will keep receiving positional
       arguments.

    .. attribute:: posarg_only
       :annotation: = False

       Arguments will always be processed as positional when this is set to
       `True`.

    .. attribute:: skip
       :annotation: = 0

       Amount of arguments to skip.

    .. attribute:: unsatisfied
       :annotation: = set(<required parameters>)

       Required parameters that haven't yet been satisfied.

    """


    def __init__(self, sig, args, name):
        self.sig = sig
        self.name = name
        self.in_args = args
        self.func = None
        self.post_name = []
        self.args = []
        self.kwargs = {}

        self.sticky = None
        self.posarg_only = False
        self.skip = 0
        self.unsatisfied = set(self.sig.required)

        posparam = iter(self.sig.positional)

        with _SeekFallbackCommand():
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
