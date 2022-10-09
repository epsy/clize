# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

"""
interpret function signatures and read commandline arguments
"""

import itertools
import inspect
import os
import typing
from functools import partial, wraps
import pathlib
import warnings

import attr
import attrs
from sigtools import modifiers, signature

from clize import errors, util


class ClizeAnnotations:
    def __init__(self, annotations):
        self.clize_annotations = util.maybe_iter(annotations)

    def __repr__(self):
        arg = ', '.join(repr(item) for item in self.clize_annotations)
        return f"clize.Clize[{arg}]"

    @classmethod
    def get_clize_annotations(cls, top_level_annotation):
        if top_level_annotation is inspect.Parameter.empty:
            return ParsedAnnotation()

        if _is_annotated_instance(top_level_annotation):
            return ParsedAnnotation(top_level_annotation.__origin__, tuple(_extract_annotated_metadata(top_level_annotation.__metadata__)))

        return ParsedAnnotation(clize_annotations=util.maybe_iter(top_level_annotation))


@attrs.define
class ParsedAnnotation:
    type_annotation: typing.Any = inspect.Parameter.empty
    clize_annotations: typing.Tuple = ()


def _is_annotated_instance(annotation):
    try:
        annotation.__origin__
        annotation.__metadata__
    except AttributeError:
        return False
    else:
        return True


def _extract_annotated_metadata(metadata):
    for item in metadata:
        if _is_annotated_instance(item):
            yield from _extract_annotated_metadata(item.__metadata__)
        elif isinstance(item, ClizeAnnotations):
            yield from item.clize_annotations


class ParameterFlag(object):
    def __init__(self, name, prefix='clize.Parameter'):
        self.name = name
        self.prefix = prefix

    def __repr__(self):
        return '{0.prefix}.{0.name}'.format(self)


class Parameter(object):
    """Represents a CLI parameter.

    :param str display_name: The 'default' representation of the parameter.
    :param bool undocumented:
        If true, hides the parameter from the command help.
    :param last_option: If `True`, the parameter will set the `.posarg_only`
        flag on the bound arguments.

    Also available as `clize.Parameter`.
    """

    L = LAST_OPTION = ParameterFlag('LAST_OPTION')
    """Annotate a parameter with this and all following arguments will be
    processed as positional."""

    I = IGNORE = ParameterFlag('IGNORE')
    """Annotate a parameter with this and it will be dropped from the
    resulting CLI signature."""

    U = UNDOCUMENTED = ParameterFlag('UNDOCUMENTED')
    """Parameters annotated with this will be omitted from the
    documentation (``--help``)."""

    R = REQUIRED = ParameterFlag('REQUIRED')
    """Annotate a parameter with this to force it to be required.

    Mostly only useful for ``*args`` parameters. In other cases, simply don't
    provide a default value."""

    @attrs.define
    class cli_default:
        value: typing.Any
        convert: bool = attrs.field(default=True, kw_only=True)

        def value_after_conversion(self, converter):
            if self.convert:
                return converter(self.value)
            else:
                return self.value

    required = False
    """Is this parameter required?"""

    is_alternate_action = False
    """Should this parameter appear as an alternate action or as a regular
    parameter?"""

    extras = ()
    """Iterable of extra parameters this parameter incurs"""

    def __init__(self, display_name, undocumented=False, last_option=None):
        self.display_name = display_name
        """The name used in printing this parameter."""
        self.undocumented = undocumented
        """If true, this parameter is hidden from the documentation."""
        self.last_option = last_option
        """If true, arguments after this parameter is triggered will all be
        processed as positional."""

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

        The base implementation of this method applies the `last_option`
        setting if applicable and discards itself from
        `CliBoundArguments.unsatisfied`
        """
        if self.last_option:
            ba.posarg_only = True
        ba.unsatisfied.discard(self)
        ba.not_provided.discard(self)

    def unsatisfied(self, ba):
        """Called after processing arguments if this parameter required
        and not discarded from `.CliBoundArguments.unsatisfied`."""
        return True

    def post_parse(self, ba):
        """Called after all arguments are processed successfully."""

    def get_all_names(self):
        """Return a string with all of this parameter's names."""
        return self.get_full_name()

    def get_full_name(self):
        """Return a string that designates this parameter."""
        return self.display_name

    def __str__(self):
        """Return a string to represent this parameter in cli usage."""
        if self.required:
            return self.get_full_name()
        else:
            return '[{0}]'.format(self.get_full_name())

    def show_help(self, desc, after, f, cols):
        """Called by `~clize.help.ClizeHelp` to produce the parameter's
        description in the help output."""
        return (
            self.get_all_names(), (
                getattr(self, 'description', None) or desc
                ) + self.show_help_parens()
            )

    def show_help_parens(self):
        """Return a string to complement a parameter's description in the
        ``--help`` output."""
        s = ', '.join(self.help_parens())
        if s:
            return ' ({0})'.format(s)
        return ''

    def help_parens(self):
        """Return an iterable of strings to complement a parameter's
        description in the ``--help`` output. Used by `.show_help_parens`"""
        return ()

    def prepare_help(self, helper):
        """Called by `~clize.help.ClizeHelp` to allow parameters to
        complement the help.

        :param: clize.help.ClizeHelp helper: The object charged with
            displaying the help.
        """


class ParameterWithSourceEquivalent(Parameter):
    """Parameter that relates to a function parameter in the source.

    :param str argument_name: The name of the parameter.
    """
    def __init__(self, argument_name, **kwargs):
        super(ParameterWithSourceEquivalent, self).__init__(**kwargs)
        self.argument_name = argument_name


class HelperParameter(Parameter):
    """Parameter that doesn't appear in CLI signatures but is used for
    instance as the ``.sticky`` attribute of the bound arguments."""

    def __init__(self, **kwargs):
        super(HelperParameter, self).__init__(
            display_name='<internal>', **kwargs)


def value_converter(func=None, *, name=None, convert_default=None, convert_default_filter=lambda s: isinstance(s, str)):
    """Callables decorated with this can be used as a value converter.

    :param str name: Use this name to designate the parameter value type.

        This should be in uppercase, with as few words as possible and no word
        delimiters.

        The default is the name of the decorated function or type, modified to
        follow this rule.

    :param bool convert_default: *Deprecated*: use the `Parameter.cli_default()` annotation instead.

        If true, the value converter will be called
        with the default parameter value if none was supplied. Otherwise, the
        default parameter is used as-is.

        Make sure to handle `None` appropriately if you override this.

    :param function convert_convert_default_filter: *Deprecated* Avoid ``convert_default`` completely.

        If ``convert_default`` is true, controls when the converter is called.
        The converter is used only if the given function returns true.

    See :ref:`value converter`.
    """
    if convert_default is not None:
        warnings.warn("The convert_default parameter of value_converter is deprecated.  "
                      "Direct users to use clize.Parameter.cli_default() instead.",
                      DeprecationWarning,
                      stacklevel=2)
    def decorate(func):
        info = {
            'name': util.name_type2cli(func) if name is None else name,
            'convert_default': convert_default,
            'convert_default_filter': convert_default_filter,
        }
        try:
            func._clize__value_converter = info
            return func
        except (TypeError, AttributeError):
            @wraps(func)
            def _wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            _wrapper._clize__value_converter = info
            return _wrapper
    if func is not None:
        return decorate(func)
    return decorate


@value_converter(name='STR')
def identity(x=None):
    return x


@value_converter(name='BYTES')
def convert_back_to_bytes(arg):
    return os.fsencode(arg)


@value_converter(name='BOOL')
def is_true(arg):
    return arg.lower() not in ('', '0', 'n', 'no', 'f', 'false')


@value_converter(name='PATH')
def concrete_path_converter(arg):
    return pathlib.Path(arg)


_implicit_converters = {
    int: int,
    float: float,
    bool: is_true,
    str: identity,
    bytes: convert_back_to_bytes,
    pathlib.PurePath: concrete_path_converter
}


def get_value_converter(annotation):
    try:
        return _implicit_converters[annotation]
    except KeyError:
        pass
    if getattr(annotation, '_clize__value_converter', False):
        return annotation
    if isinstance(annotation, type):
        for ic in _implicit_converters:
            if issubclass(annotation, ic):
                return _implicit_converters[ic]
    raise ValueError('{0!r} is not a value converter'.format(annotation))


class ParameterWithValue(Parameter):
    """A parameter that takes a value from the arguments, with possible
    default and/or conversion.

    :param callable conv: A callable to convert the value or raise `ValueError`.
        Defaults to `.identity`.
    :param default: A default value for the parameter or `.util.UNSET`.
    """

    def __init__(self, conv=identity, default=util.UNSET,
                       cli_default=util.UNSET,
                       **kwargs):
        super(ParameterWithValue, self).__init__(**kwargs)
        self.conv = conv
        """The function used for coercing the value into the desired format or
        type."""
        self.default = default
        """The default value used for the parameter, or `.util.UNSET` if there
        is no default value. Usually only used for displaying the help."""
        self.cli_default = cli_default
        """The default value used for the parameter in the CLI,
        or `.util.UNSET` if there is no default value.
        Converted by ``self.conv`` before insertion."""

    @property
    def required(self):
        """Tells if the parameter has no default value."""
        return self.default is util.UNSET and self.cli_default is util.UNSET

    def read_argument(self, ba, i):
        """Uses `.get_value`, `.coerce_value` and `.set_value` to process
        an argument"""
        self.set_value(ba, self.coerce_value(self.get_value(ba, i), ba))

    def set_value(self, ba, value):
        """Save the value for this parameter

        Usually accomplished by adding to `ba.args <CliBoundArguments.args>` or
        `ba.kwargs <CliBoundArguments.kwargs>`.
        """
        raise NotImplementedError

    def coerce_value(self, arg, ba):
        """Coerces ``arg`` using the `.conv` function. Raises
        `.errors.BadArgumentFormat` if the coercion function raises
        `ValueError`.
        """
        try:
            ret = self.conv(arg)
        except errors.CliValueError as e:
            exc = errors.BadArgumentFormat(e)
            exc.__cause__ = e
            raise exc
        except ValueError as e:
            exc = errors.BadArgumentFormat(repr(arg))
            exc.__cause__ = e
            raise exc
        else:
            return ret

    def get_value(self, ba, i):
        """Retrieves the "value" part of the argument in ``ba`` at
        position ``i``."""
        return ba.in_args[i]

    def help_parens(self):
        """Shows the default value in the parameter description."""
        if self.cli_default is not util.UNSET:
            if self.cli_default.value is not None:
                yield 'default: ' + str(self.cli_default.value)
        elif self.default is not util.UNSET and self.default is not None:
            yield 'default: ' + str(self.default)

    def post_parse(self, ba):
        super(ParameterWithValue, self).post_parse(ba)
        if self in ba.not_provided:
            default_value = self.default_value_if_non_source_default(ba)
            if default_value is not util.UNSET:
                self.set_value(ba, default_value)

    def default_value_if_non_source_default(self, ba):
        if self.cli_default is not util.UNSET:
            return self.cli_default.value_after_conversion(partial(self.coerce_value, ba=ba))
        if self.default is not util.UNSET:
            try:
                info = self.conv._clize__value_converter
            except AttributeError:
                pass
            else:
                if info['convert_default'] and info['convert_default_filter'](self.default):
                    return self.conv(self.default)
        return util.UNSET

    def default_value(self, ba):
        converted_default = self.default_value_if_non_source_default(ba)
        if converted_default is not util.UNSET:
            return converted_default
        return self.default



class NamedParameter(Parameter):
    """Equivalent of a keyword-only parameter in Python.

    :param aliases: The arguments that trigger this parameter. The first alias
        is used to refer to the parameter. The first one is picked as
        `.display_name` if unspecified.
    :type aliases: sequence of strings
    """
    def __init__(self, aliases, **kwargs):
        kwargs.setdefault('display_name', aliases[0])
        super(NamedParameter, self).__init__(**kwargs)
        self.aliases = aliases
        """The parameter's aliases, eg. "--option" and "-o"."""

    __key_count = itertools.count()
    @classmethod
    def alias_key(cls, name):
        """Sort key function to order aliases in source order, but with short
        forms(one dash) first."""
        return len(name) - len(name.lstrip('-')), next(cls.__key_count)

    def get_all_names(self):
        """Retrieves all aliases."""
        return ', '.join(sorted(self.aliases, key=self.alias_key)
            )

    @property
    def short_name(self):
        """Retrieves the shortest alias for displaying the parameter
        signature."""
        return min(self.aliases, key=len)

    def get_full_name(self):
        """Uses the shortest name instead of the display name."""
        return self.short_name

    def redispatch_short_arg(self, rest, ba, i):
        """Processes the rest of an argument as if it was a new one prefixed
        with one dash.

        For instance when ``-a`` is a flag in ``-abcd``, the object implementing
        it will call this to proceed as if ``-a -bcd`` was passed."""
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
        ba.not_provided.discard(nparam)

    def get_value(self, ba, i):
        """Fetches the value after the ``=`` (``--opt=val``) or in the
        next argument (``--opt val``)."""
        arg = super(NamedParameter, self).get_value(ba, i)
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
        ba.skip = not glued
        return val


class OptionParameter(NamedParameter, ParameterWithValue,
                      ParameterWithSourceEquivalent):
    """A named parameter that takes an argument."""

    def read_argument(self, ba, i):
        """Stores the argument in `CliBoundArguments.kwargs` if it isn't
        already present."""
        if self.argument_name in ba.kwargs:
            raise errors.DuplicateNamedArgument()
        super(OptionParameter, self).read_argument(ba, i)

    def set_value(self, ba, value):
        """Set the value in `ba.kwargs <CliBoundArguments.kwargs>`"""
        ba.kwargs[self.argument_name] = value

    def format_type(self):
        """Returns a string designation of the value type."""
        return util.name_type2cli(self.conv)

    def format_argument(self, long_alias):
        """Format the value type for the parameter"""
        return ('=' if long_alias else ' ') + self.format_type()

    def get_all_names(self):
        """Appends the value type to all aliases."""
        names = super(OptionParameter, self).get_all_names()
        long_alias = any(alias.startswith('--') for alias in self.aliases)
        return names + self.format_argument(long_alias)

    def get_full_name(self):
        """Appends the value type to the shortest alias."""
        sn = super(OptionParameter, self).get_full_name()
        short_alias = any(
            not alias.startswith('--') for alias in self.aliases)
        return sn + self.format_argument(not short_alias)


class FlagParameter(OptionParameter):
    """A named parameter that takes no argument.

    :param value: The value when the argument is present.
    :param false_value: The value when the argument is given one of the
        false value triggers using ``--param=xyz``.
    """

    required = False

    false_triggers = '0', 'n', 'no', 'f', 'false'
    """Values for which ``--flag=X`` will consider the argument false and
    will pass `.false_value` to the function. In all other cases `.value`
    is passed."""

    def __init__(self, value, **kwargs):
        super(FlagParameter, self).__init__(**kwargs)
        self.value = value
        """The value passed to the function if the flag is triggered without
        a specified value."""

    def read_argument(self, ba, i):
        """Overrides `NamedParameter`'s value-getting behavior to allow no
        argument to be passed after the flag is named."""
        arg = ba.in_args[i]
        if arg[1] == '-':
            name, sep, val = arg.partition('=')
            self.set_value(ba, self.coerce_value(val, ba) if sep else self.value)
        else:
            self.set_value(ba, self.value)
            self.redispatch_short_arg(arg[2:], ba, i)

    def format_argument(self, long_alias):
        """Formats the argument value type for usage messages.

        This is usually empty unless the flag uses a non-boolean flag.
        """
        if not long_alias or self.conv == is_true:
            return ''
        return ('[=' if long_alias else ' [') + self.format_type() + ']'


def split_int_rest(s):
    for i, c, in enumerate(s):
        if not c.isdigit() and c != '-':
            return s[:i], s[i:]
    return s, ''


class IntOptionParameter(OptionParameter):
    """A named parameter that takes an integer as argument. The short form
    of it can be chained with the short form of other named parameters."""

    def read_argument(self, ba, i):
        """Handles redispatching after a numerical value."""
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
        self.set_value(ba, self.coerce_value(val, ba))

        self.redispatch_short_arg(rest, ba, i)


class PositionalParameter(ParameterWithValue, ParameterWithSourceEquivalent):
    """Equivalent of a positional-only parameter in Python."""

    def set_value(self, ba, val):
        """Stores the argument at the appropriate position
        in `ba.args <CliBoundArguments.args>`.

        If `ba.args <CliBoundArguments.args>` is not filled up to this
        parameter's position yet, it will be filled with default values.

        :raises ValueError: when setting a parameter after unsatisfied
            parameters with no default value.
        """
        matched = util.zip_longest(ba.sig.positional, ba.args, fillvalue=util.UNSET)
        for i, (param, arg) in enumerate(matched):
            if param is self:
                if arg is util.UNSET:
                    ba.args.append(val)
                else:
                    ba.args[i] = val
                return
            else:
                if arg is util.UNSET:
                    default_value = param.default_value(ba)
                    if default_value is not util.UNSET:
                        ba.args.append(default_value)
                        # ba.args.append(param.cli_default.value_after_conversion(partial(self.coerce_value, ba=ba)))
                    else:
                        raise ValueError(
                            "Can't set parameters after required parameters")
        else:
            raise ValueError("{!r} not present in signature".format(self))

    def help_parens(self):
        """Puts the value type in parenthesis since it isn't shown in
        the parameter's signature."""
        if self.conv is not identity:
            yield 'type: ' + util.name_type2cli(self.conv)
        for s in super(PositionalParameter, self).help_parens():
            yield s


class MultiParameter(ParameterWithValue):
    """Parameter that can collect multiple values."""

    def __init__(self, min, max, **kwargs):
        super(MultiParameter, self).__init__(**kwargs)
        self.min = min
        """The minimum amount of values this parameter accepts."""
        self.max = max
        """The maximum amount of values this parameter accepts."""

    @property
    def required(self):
        """Returns if there is a minimum amount of values required."""
        return self.min

    def get_collection(self, ba):
        """Return an object that new values will be appended to."""
        raise NotImplementedError

    def read_argument(self, ba, i):
        """Reset read_argument to avoid hitting `OptionParameter.read_argument`
        which checks for duplicate parameters"""
        self.set_value(ba, self.coerce_value(self.get_value(ba, i), ba))

    def set_value(self, ba, val):
        """Adds passed argument to the collection returned
        by `get_collection`."""
        col = self.get_collection(ba)
        col.append(val)
        if self.min <= len(col):
            ba.unsatisfied.discard(self)
        if self.max is not None and self.max < len(col):
            raise errors.TooManyValues

    def apply_generic_flags(self, ba):
        """Doesn't automatically mark the parameter as satisfied."""
        if self.last_option:
            ba.posarg_only = True
        ba.not_provided.discard(self)

    def unsatisfied(self, ba):
        """Lets `errors.MissingRequiredArguments` be raised or raises
        `errors.NotEnoughValues` if arguments were passed but not enough
        to meet `.min`."""
        if not ba.args or len(ba.unsatisfied) > 1:
            return True
        raise errors.NotEnoughValues

    def get_full_name(self):
        """Adds an ellipsis to the parameter name."""
        return super(MultiParameter, self).get_full_name() + '...'


class ExtraPosArgsParameter(MultiParameter, PositionalParameter):
    """Parameter that forwards all remaining positional arguments to the
    callee.

    Used to convert ``*args``-like parameters.
    """

    def __init__(self, required=False, min=None, max=None, **kwargs):
        min = bool(required) if min is None else min
        super(ExtraPosArgsParameter, self).__init__(min=min, max=max, **kwargs)

    def get_collection(self, ba):
        """Uses `CliBoundArguments.args` to collect the remaining arguments."""
        return ba.args

    def apply_generic_flags(self, ba):
        """Sets itself as sticky parameter so that `errors.TooManyArguments`
        is not raised when processing further parameters."""
        super(ExtraPosArgsParameter, self).apply_generic_flags(ba)
        ba.sticky = self


class AppendArguments(HelperParameter, MultiParameter):
    """Helper parameter that collects multiple values to be passed as
    positional arguments to the callee.

    Similar to `ExtraPosArgsParameter` but does not correspond to a parameter
    in the source."""

    def __init__(self, **kwargs):
        super(AppendArguments, self).__init__(min=0, max=None, **kwargs)

    def get_collection(self, ba):
        """Uses `CliBoundArguments.args` to collect the remaining arguments."""
        return ba.args


class IgnoreAllArguments(HelperParameter, Parameter):
    """Helper parameter for `.FallbackCommandParameter` that ignores the
    remaining arguments."""

    def read_argument(self, ba, i):
        """Does nothing, ignoring all arguments processed."""
        pass


class FallbackCommandParameter(NamedParameter):
    """Parameter that sets an alternative function when triggered. When used
    as an argument other than the first all arguments are discarded."""

    is_alternate_action = True

    def __init__(self, func, **kwargs):
        super(FallbackCommandParameter, self).__init__(**kwargs)
        self.func = func
        """The function that will be called if this parameter is mentioned."""

    @util.property_once
    def description(self):
        """Use `.func`'s docstring to provide the parameter
        description."""
        try:
            return self.func.helper.description
        except AttributeError:
            pass

    def read_argument(self, ba, i):
        """Clears all processed arguments, sets up `.func` to be called later,
        and lets all remaining arguments be collected as positional if this
        was the first argument."""
        ba.args[:] = [ba.name + ' ' + self.display_name]
        ba.kwargs.clear()
        ba.post_name.append(ba.in_args[i])
        ba.func = self.func
        ba.posarg_only = True
        ba.sticky = IgnoreAllArguments() if i else AppendArguments()


class AlternateCommandParameter(FallbackCommandParameter):
    """Parameter that sets an alternative function when triggered. Cannot
    be used as any argument but the first."""

    def read_argument(self, ba, i):
        """Raises an error when this parameter is used after other arguments
        have been given."""
        if i:
            raise errors.ArgsBeforeAlternateCommand(self)
        return super(AlternateCommandParameter, self).read_argument(ba, i)


@modifiers.kwoargs(start='name')
def parameter_converter(obj=None, name=None):
    """Decorates a callable to be interpreted as a parameter converter
    when passed as an annotation.

    It will be called with an `inspect.Parameter` object and a sequence of
    objects passed as annotations, without the parameter converter itself.
    It is expected to return a `clize.parser.Parameter` instance or
    `Parameter.IGNORE`."""
    if obj is None:
        return partial(parameter_converter, name=name)
    obj._clize__parameter_converter = True
    if name:
        obj.__name__ = name
    elif not getattr(obj, '__name__', None):
        warnings.warn(
            "Nameless parameter converter {!r}. "
            "Please specify one using the 'name' parameter of "
            "parameter_converter".format(obj),
            RuntimeWarning, stacklevel=3)
    return obj


def is_parameter_converter(obj):
    return getattr(obj, '_clize__parameter_converter', False)


def unimplemented_parameter(argument_name, **kwargs):
    raise ValueError(
        "This converter cannot convert parameter {0!r} to a CLI parameter"
        .format(argument_name))


@modifiers.autokwoargs
def use_class(
        name=None,
        pos=unimplemented_parameter, varargs=unimplemented_parameter,
        named=unimplemented_parameter, varkwargs=unimplemented_parameter,
        kwargs={}):
    """Creates a parameter converter similar to the default converter that
    picks one of 4 factory functions depending on the type of parameter.

    :param name str: A name to set on the parameter converter.
    :param pos: The parameter factory for positional parameters.
    :param varargs: The parameter factory for ``*args``-like parameters.
    :param named: The parameter factory for keyword parameters.
    :param varkwargs: The parameter factory for ``**kwargs``-like parameters.
    :type pos: callable that returns a `Parameter` instance
    :type varargs: callable that returns a `Parameter` instance
    :type named: callable that returns a `Parameter` instance
    :type varkwargs: callable that returns a `Parameter` instance
    :param collections.abc.Mapping kwargs: additional arguments to pass
        to the chosen factory.
    """
    conv = partial(_use_class, pos, varargs, named, varkwargs, kwargs)
    if not name:
        warnings.warn(
            "Nameless parameter converter. Please specify the name argument "
            "when calling use_class",
            RuntimeWarning, stacklevel=3)
        name = repr(conv)
    return parameter_converter(conv, name=name)


@modifiers.autokwoargs
def use_mixin(cls, kwargs={}, name=None):
    """Like ``use_class``, but creates classes inheriting from ``cls`` and
    one of ``PositionalParameter``, ``ExtraPosArgsParameter``, and
    ``OptionParameter``

    :param cls: The class to use as mixin.
    :param collections.abc.Mapping kwargs: additional arguments to pass
        to the chosen factory.
    :param name: The name to use for the converter.  Uses ``cls``'s name
        if unset.
    """
    class _PosWithMixin(cls, PositionalParameter): pass
    class _VarargsWithMixin(cls, ExtraPosArgsParameter): pass
    class _NamedWithMixin(cls, OptionParameter): pass
    if not name:
        name = cls.__name__
    return use_class(pos=_PosWithMixin, varargs=_VarargsWithMixin,
                     named=_NamedWithMixin,
                     name=name, kwargs=kwargs)


def _use_class(pos_cls, varargs_cls, named_cls, varkwargs_cls, kwargs,
               param, annotations, *, type_annotation):
    named = param.kind in (param.KEYWORD_ONLY, param.VAR_KEYWORD)
    aliases = [util.name_py2cli(param.name, named)]
    default = util.UNSET
    conv = identity

    kwargs = dict(
        kwargs,
        argument_name=param.name,
        undocumented=Parameter.UNDOCUMENTED in annotations,
        )

    if param.default is not param.empty:
        default = param.default

    if Parameter.REQUIRED in annotations:
        kwargs['required'] = True

    if Parameter.LAST_OPTION in annotations:
        kwargs['last_option'] = True

    exclusive_converter = None
    set_converter = False

    if type_annotation != param.empty:
        try:
            # we specifically don't set exclusive_converter
            # so that clize annotations can set a different converter
            conv = get_value_converter(type_annotation)
        except ValueError:
            pass
        else:
            set_converter = True

    for thing in annotations:
        if isinstance(thing, Parameter):
            return thing
        if callable(thing):
            if is_parameter_converter(thing):
                raise ValueError(
                    "Parameter converter {!r} must be the first element "
                    "of a parameter's annotation"
                    .format(getattr(thing, '__name__', thing)))
            try:
                conv = get_value_converter(thing)
            except ValueError:
                pass
            else:
                if exclusive_converter is not None:
                    raise ValueError(
                        "Value converter specified twice in annotation: "
                        f"{exclusive_converter.__name__} {thing.__name__}"
                    )
                exclusive_converter = thing
                set_converter = True
                continue
        if isinstance(thing, str):
            if not named:
                raise ValueError("Cannot give aliases for a positional "
                                 "parameter.")
            if len(thing.split()) > 1:
                raise ValueError("Cannot have whitespace in aliases.")
            alias = util.name_py2cli(thing, named, fixcase=False)
            if alias in aliases:
                raise ValueError("Duplicate alias " + repr(thing))
            aliases.append(alias)
            continue
        if isinstance(thing, ParameterFlag):
            continue
        if isinstance(thing, Parameter.cli_default):
            kwargs['cli_default'] = thing
            continue
        raise ValueError(
            "Unknown annotation {!r}\n"
            "If you intended for it to be a value or parameter converter, "
            "make sure the appropriate decorator was applied."
            .format(thing))

    kwargs['default'] = default if not kwargs.get('required') else util.UNSET
    kwargs['conv'] = conv
    if not set_converter and default is not util.UNSET and default is not None:
        try:
            kwargs['conv'] = get_value_converter(type(default))
            set_converter = True
        except ValueError:
            raise ValueError(
                "Cannot find value converter for default value {!r}. "
                "Please specify one as an annotation.\n"
                "If the default value's type should be used to "
                "convert the value, make sure it is decorated "
                "with clize.parser.value_converter()"
                .format(default))
    if not set_converter and type_annotation is not inspect.Parameter.empty:
        raise ValueError(
            f"Cannot find a value converter for type {type_annotation}. "
            "Please specify one as an annotation.\n"
            "If the type should be used to "
            "convert the value, make sure it is decorated "
            "with clize.parser.value_converter()"
        )

    if kwargs['default'] is not util.UNSET:
        try:
            info = getattr(kwargs['conv'], "_clize__value_converter")
        except AttributeError:
            pass
        else:
            if info["convert_default"] and info["convert_default_filter"](kwargs["default"]):
                warnings.warn(
                    f"For parameter '{param.name}':  "
                    "Default argument conversion is deprecated.  "
                    "Instead, please use clize.Parameter.cli_default(value) "
                    "when you need a default value that "
                    "is converted the same way as a value passed in from the command line, "
                    "as opposed to values passed in from calling the function in Python, "
                    "which aren't converted by Clize.",
                    DeprecationWarning
                )

    if named:
        kwargs['aliases'] = aliases
        if param.kind == param.VAR_KEYWORD:
            return varkwargs_cls(**kwargs)
        return named_cls(**kwargs)
    else:
        kwargs['display_name'] = util.name_py2cli(param.name)
        if param.kind == param.VAR_POSITIONAL:
            return varargs_cls(**kwargs)
        return pos_cls(**kwargs)

def pos_parameter(required=False, **kwargs):
    return PositionalParameter(**kwargs)

def named_parameter(**kwargs):
    if kwargs['default'] is False and kwargs['conv'] is is_true:
        del kwargs['default']
        return FlagParameter(value=True, **kwargs)
    elif kwargs['conv'] is _implicit_converters[int]:
        return IntOptionParameter(**kwargs)
    else:
        return OptionParameter(**kwargs)

default_converter = use_class(
    pos=pos_parameter, varargs=ExtraPosArgsParameter,
    named=named_parameter,
    name='default_converter')
"""The default parameter converter. It is described in detail in :ref:`default-converter`."""


def _develop_extras(params):
    for param in params:
        yield param
        for subparam in _develop_extras(param.extras):
            yield subparam


class CliSignature(object):
    """A collection of parameters that can be used to translate CLI arguments
    to function arguments.

    :param iterable parameters: The parameters to use.

    .. attribute:: converter
       :annotation: = clize.parser.default_converter

       The converter used by default in case none is present in the
       annotations.

    .. attribute:: parameters

        An ordered dict of all parameters of this cli signature.

    .. attribute:: positional

        List of positional parameters.

    .. attribute:: alternate

        List of parameters that initiate an alternate action.

    .. attribute:: named

        List of named parameters that aren't in `.alternate`.

    .. attribute:: aliases
        :annotation: = {}

        Maps parameter names to `NamedParameter` instances.

    .. attribute:: required
        :annotation: = set()

        A set of all required parameters.
    """

    converter = default_converter

    def __init__(self, parameters):
        params = self.parameters = util.OrderedDict()
        pos = self.positional = []
        named = self.named = []
        alt = self.alternate = []
        aliases = self.aliases = {}
        required = self.required = set()
        optional = self.optional = set()
        for param in _develop_extras(parameters):
            required_ = getattr(param, 'required', False)
            aliases_ = getattr(param, 'aliases', None)

            if required_:
                required.add(param)
            else:
                optional.add(param)

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

            if param.is_alternate_action:
                alt.append(param)
            elif aliases_ is not None:
                named.append(param)
            else:
                pos.append(param)
            params[getattr(param, 'argument_name', param.display_name)] = param

    @classmethod
    def from_signature(cls, sig, extra=(), **kwargs):
        """Takes a signature object and returns an instance of this class
        deduced from it.

        :param inspect.Signature sig: The signature object to use.
        :param iterable extra: Extra parameter instances to include.
        """
        return cls(
            parameters=itertools.chain(
                filter(lambda x: x is not Parameter.IGNORE,
                    (cls.convert_parameter(param)
                    for param in sig.parameters.values())
                ), extra), **kwargs)

    @classmethod
    def convert_parameter(cls, param):
        """Convert a Python parameter to a CLI parameter."""
        param_annotation = param.upgraded_annotation.source_value()
        ca = ClizeAnnotations.get_clize_annotations(param_annotation)
        annotations = ca.clize_annotations
        type_annotation = ca.type_annotation

        if Parameter.IGNORE in annotations:
            return Parameter.IGNORE

        for i, annotation in enumerate(annotations):
            if getattr(annotation, '_clize__parameter_converter', False):
                conv = annotation
                annotations = annotations[:i] + annotations[i+1:]
                break
        else:
            conv = cls.converter

        try:
            return conv(param, annotations, type_annotation=type_annotation)
        except TypeError as e:
            if "type_annotation" in signature(conv).parameters:
                raise e
            else:
                result = conv(param, annotations)
                name = getattr(conv, "__name__", repr(conv))
                while isinstance(conv, partial):
                    conv = conv.func
                impl_name = getattr(conv, "__qualname__", name)
                module = getattr(conv, "__module__")
                if module:
                    impl_name = f"{module}.{impl_name}"
                warnings.warn(
                    (
                        "Clize 6.0 will require parameter converters "
                        "to support the 'type_annotation' keyword argument: "
                        f"converter '{name}' ({impl_name}) should be updated to accept it"
                    ),
                    DeprecationWarning,
                )
                return result

    def read_arguments(self, args, name):
        """Returns a `.CliBoundArguments` instance for this CLI signature
        bound to the given arguments.

        :param sequence args: The CLI arguments, minus the script name.
        :param str name: The script name.
        """
        ba = CliBoundArguments(self, args, name)
        ba.process_arguments()
        return ba

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
                ba.not_provided.clear()
                return True


@attr.s
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

    .. attribute:: meta
        :annotation: = {}

        A dict for parameters to store data for the duration of the
        argument processing.

    .. attribute:: func
        :annotation: = None

        If not `None`, replaces the target function.

    .. attribute:: post_name
        :annotation: = []

        List of words to append to the script name when passed to the target
        function.

    The following attributes only exist while arguments are being processed:

    .. attribute:: posparam
       :annotation: = iter(sig.positional)

       The iterator over the positional parameters used to process positional
       arguments.

    .. attribute:: namedparam
       :annotation: = dict(sig.aliases)

       The `dict` used to look up named parameters from their names.

       It is copied here so that the argument parsing process may add or remove
       parameters without affecting the original signature.

    .. attribute:: unsatisfied
       :annotation: = set(sig.required)

       Required parameters that haven't yet been satisfied.

    .. attribute:: not_provided
       :annotation: = set(sig.optional)

       Optional parameters that haven't yet received a value.

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

    """

    threshold = 0.75
    """Similarity threshold below which argument suggestions are dropped. Used
    when the user enters an incorrect argument and we try to suggest a valid
    argument instead."""

    sig = attr.ib()
    in_args: typing.Tuple = attr.ib(converter=tuple)
    name = attr.ib()

    func = attr.ib(default=None)
    post_name = attr.ib(default=attr.Factory(list))
    args = attr.ib(default=attr.Factory(list))
    kwargs = attr.ib(default=attr.Factory(dict))
    meta = attr.ib(default=attr.Factory(dict))

    posparam = attr.ib(init=False)
    namedparams = attr.ib(init=False)
    unsatisfied = attr.ib(init=False)
    not_provided = attr.ib(init=False)
    posarg_only = attr.ib(init=False)
    skip = attr.ib(init=False)

    def process_arguments(self):
        """Process the arguments in `.in_args`, setting the `.func`,
        `.post_name`, `.args` and `.kwargs` attributes as a result.

        This methods reads `str`'s from `.in_args`. For each one, it finds the
        relevant `Parameter` instance in `.posparam` or `.namedparam` and
        delegates processing to it """
        self.posparam = iter(self.sig.positional)
        self.namedparams = dict(self.sig.aliases)
        self.unsatisfied = set(self.sig.required)
        self.not_provided = set(self.sig.optional)
        self.sticky = None
        self.posarg_only = False
        self.skip = 0

        with _SeekFallbackCommand():
            for i, arg in enumerate(self.in_args):
                if self.skip > 0:
                    self.skip -= 1
                    continue
                with errors.SetArgumentErrorContext(pos=i, val=arg, ba=self):
                    if self.posarg_only or len(arg) < 2 or arg[0] != '-':
                        if self.sticky is not None:
                            param = self.sticky
                        else:
                            try:
                                param = next(self.posparam)
                            except StopIteration:
                                exc = errors.TooManyArguments(
                                    self.in_args[i:])
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
                            param = self.namedparams[name]
                        except KeyError:
                            raise errors.UnknownOption(name)
                    with errors.SetArgumentErrorContext(param=param):
                        param.read_argument(self, i)
                        param.apply_generic_flags(self)

        if not self.func:
            if self.unsatisfied:
                unsatisfied = []
                for p in self.unsatisfied:
                    with errors.SetArgumentErrorContext(param=p):
                        if p.unsatisfied(self):
                            unsatisfied.append(p)
                if unsatisfied:
                    raise errors.MissingRequiredArguments(unsatisfied)

            for p in self.sig.parameters.values():
                p.post_parse(self)

        del self.sticky, self.posarg_only, self.skip, self.unsatisfied, self.not_provided

    def get_best_guess(self, passed_in_arg):
        return util.closest_option(passed_in_arg, list(self.sig.aliases))

    def __iter__(self):
        yield self.func
        yield self.post_name
        yield self.args
        yield self.kwargs
