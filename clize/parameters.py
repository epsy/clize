# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import inspect
from functools import update_wrapper

from sigtools import modifiers, specifiers, signatures

from clize import parser, errors, util


class _ShowList(BaseException):
    pass


class MappedParameter(parser.ParameterWithValue):
    def __init__(self, list_name, values, case_sensitive, **kwargs):
        super(MappedParameter, self).__init__(**kwargs)
        self.list_name = list_name
        self.case_sensitive = case_sensitive
        self.values = values

    def _uncase_values(self, values):
        used = set()
        for target, names, _ in values:
            for name in names:
                name_ = name.lower()
                if name_ in used:
                    raise ValueError(
                        "Duplicate allowed values for parameter {}: {}"
                        .format(self, name_))
                used.add(name_)
                yield name_, target

    def _ensure_no_duplicate_names(self, values):
        used = set()
        for value in values:
            _, names, _ = value
            for name in names:
                if name in used:
                    raise ValueError(
                        "Duplicate allowed values for parameter {}: {}"
                        .format(self, name))
                used.add(name)
            yield value

    @util.property_once
    def values_table(self):
        if not self.case_sensitive:
            try:
                new_values = dict(self._uncase_values(self.values))
            except ValueError:
                if self.case_sensitive is not None:
                    raise
                self.case_sensitive = True
            else:
                self.case_sensitive = False
                return new_values
        return dict(
            (name, target)
            for target, names, _ in self._ensure_no_duplicate_names(self.values)
            for name in names)

    def coerce_value(self, value, ba):
        table = self.values_table
        key = value if self.case_sensitive else value.lower()
        if key == self.list_name:
            raise _ShowList
        try:
            return table[key]
        except KeyError:
            raise errors.BadArgumentFormat(value)

    def read_argument(self, ba, i):
        try:
            super(MappedParameter, self).read_argument(ba, i)
        except _ShowList:
            ba.args[:] = [ba.name]
            ba.kwargs.clear()
            ba.func = self.show_list
            ba.sticky = parser.IgnoreAllArguments()
            ba.posarg_only = True

    def show_list(self, name):
        f = util.Formatter()
        f.append('{name}: Possible values for {self.display_name}:'
                 .format(self=self, name=name))
        f.new_paragraph()
        with f.indent():
            with f.columns() as cols:
                for _, names, desc in self.values:
                    cols.append(', '.join(names), desc)
        f.new_paragraph()
        return str(f)

    def help_parens(self):
        backup = self.default
        try:
            for arg, keys, _ in self.values:
                if arg == self.default:
                    self.default = keys[0]
                    break
            else:
                self.default = util.UNSET
            for s in super(MappedParameter, self).help_parens():
                yield s
        finally:
            self.default = backup
        if self.list_name:
            yield 'use "{0}" for options'.format(self.list_name)


@modifiers.autokwoargs
def mapped(values, list_name='list', case_sensitive=None):
    """Creates an annotation for parameters that maps input values to Python
    objects.

    :param sequence values: A sequence of ``pyobj, names, description`` tuples.
        For each item, the user can specify a name from ``names`` and the
        parameter will receive the corresponding ``pyobj`` value.
        ``description`` is used when listing the possible values.
    :param str list_name: The value the user can use to show a list of possible
        values and their description.
    :param bool case_sensitive: Force case-sensitiveness for the input values.
        The default is to guess based on the contents of values.

    .. literalinclude:: /../examples/mapped.py
        :lines: 4-15

    """
    return parser.use_mixin(MappedParameter, kwargs={
        'case_sensitive': case_sensitive,
        'list_name': list_name,
        'values': values,
    })


def _conv_oneof(values):
    for value in values:
        if isinstance(value, str):
            yield value, [value], ''
        else:
            yield value[0], [value[0]], value[1]


@modifiers.autokwoargs
def one_of(case_sensitive=None, list_name='list', *values):
    """Creates an annotation for a parameter that only accepts the given
    values.

    :param values: ``value, description`` tuples, or just the accepted values
    :param str list_name: The value the user can use to show a list of possible
        values and their description.
    :param bool case_sensitive: Force case-sensitiveness for the input values.
        The default is to guess based on the contents of values.

    
    """
    return mapped(
        list(_conv_oneof(values)),
        case_sensitive=case_sensitive, list_name=list_name)


class MultiOptionParameter(parser.MultiParameter, parser.OptionParameter):
    """Named parameter that can collect multiple values."""

    def get_collection(self, ba):
        return ba.kwargs.setdefault(self.argument_name, [])

    def post_parse(self, ba):
        super(MultiOptionParameter, self).post_parse(ba)
        ba.kwargs.setdefault(self.argument_name, [])

    def unsatisfied(self, ba):
        if not ba.kwargs.get(self.argument_name):
            return True
        raise errors.NotEnoughValues


def multi(min=0, max=None):
    """For option parameters, allows the parameter to be repeated on the
    command-line with an optional minimum or maximum. For ``*args``-like
    parameters, just adds the optional bounds.

    .. literalinclude:: /../examples/multi.py
        :lines: 4-10
    """

    return parser.use_class(
        named=MultiOptionParameter, varargs=parser.ExtraPosArgsParameter,
        kwargs={
            'min': min,
            'max': max,
        }, name="multi")


class _ComposedProperty(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        return getattr(instance.real, self.name)

    def __set__(self, instance, value):
        return setattr(instance.real, self.name, value)

    def __delete__(self, instance):
        return delattr(instance.real, self.name)


class _SubBoundArguments(object):
    def __init__(self, real):
        self.real = real
        self.args = []
        self.kwargs = {}

    sig = _ComposedProperty('sig')
    name = _ComposedProperty('name')
    in_args = _ComposedProperty('in_args')
    func = _ComposedProperty('func')
    post_name = _ComposedProperty('post_name')
    meta = _ComposedProperty('meta')
    sticky = _ComposedProperty('sticky')
    posarg_only = _ComposedProperty('posarg_only')
    skip = _ComposedProperty('skip')
    unsatisfied = _ComposedProperty('unsatisfied')
    not_provided = _ComposedProperty('not_provided')


class _DerivBoundArguments(object):
    def __init__(self, deriv, real):
        self.real = real
        u = self.unsatisfied = set()
        n = self.not_provided = set()
        if deriv.sub_required:
            u.add(deriv)
        else:
            n.add(deriv)

    args = _ComposedProperty('args')
    kwargs = _ComposedProperty('kwargs')
    sig = _ComposedProperty('sig')
    name = _ComposedProperty('name')
    in_args = _ComposedProperty('in_args')
    func = _ComposedProperty('func')
    post_name = _ComposedProperty('post_name')
    meta = _ComposedProperty('meta')
    sticky = _ComposedProperty('sticky')
    posarg_only = _ComposedProperty('posarg_only')
    skip = _ComposedProperty('skip')


class ForwarderParameter(parser.NamedParameter,
                         parser.ParameterWithSourceEquivalent):
    def __init__(self, real, parent, **kwargs):
        super(ForwarderParameter, self).__init__(
            aliases=real.aliases, argument_name=real.argument_name,
            undocumented=True, **kwargs)
        self.real = real
        self.parent = parent
        self.orig_redispatch = real.redispatch_short_arg
        real.redispatch_short_arg = self.redispatch_short_arg

    def get_fba(self, ba):
        return self.parent.get_meta(ba).get_sub()

    def read_argument(self, ba, i):
        self.real.read_argument(self.get_fba(ba), i)

    def apply_generic_flags(self, ba):
        self.real.apply_generic_flags(self.get_fba(ba))

    def redispatch_short_arg(self, rest, ba, i):
        self.orig_redispatch(rest, ba.real, i)


def _redirect_ba(param, dap):
    if isinstance(param, parser.NamedParameter):
        return ForwarderParameter(real=param, parent=dap)
    raise ValueError("Parameter \"{0}\" cannot be used in an "
                     "argument decorator".format(param))


class _DapMeta(object):
    def __init__(self, ba, parent):
        self.ba = ba
        self.parent = parent
        self.sub = None
        self.deriv = None

    def get_sub(self):
        if self.sub is None:
            fba = self.sub = _SubBoundArguments(self.ba)
            self.ba.unsatisfied.update(self.parent.cli.required)
            self.ba.not_provided.update(self.parent.cli.optional)
            return fba
        else:
            return self.sub

    def pop_sub(self):
        s = self.sub
        self.sub = None
        return s

    def get_deriv(self):
        if self.deriv is None:
            fba = self.deriv = _DerivBoundArguments(self.parent, self.ba)
            return fba
        else:
            return self.deriv


class DecoratedArgumentParameter(parser.ParameterWithSourceEquivalent):
    required = True

    @property
    def sub_required(self):
        try:
            return self._sub_required
        except AttributeError:
            attr = super(DecoratedArgumentParameter, type(self)).required
            return attr.__get__(self, type(self))

    def __init__(self, decorator, **kwargs):
        super(DecoratedArgumentParameter, self).__init__(**kwargs)
        self.decorator = decorator
        self.cli = parser.CliSignature.from_signature(
            signatures.mask(specifiers.signature(decorator), 1))
        self.extras = [
            _redirect_ba(p, self)
            for p in self.cli.parameters.values()
            #if not isinstance(p, ForwarderParameter)
            ]
        try:
            super(DecoratedArgumentParameter, type(self)).required.__get__
        except AttributeError:
            self._sub_required = self.required
        self.required = True

    def get_meta(self, ba):
        return ba.meta.setdefault(self.argument_name, _DapMeta(ba, self))

    def coerce_value(self, arg, ba):
        val = super(DecoratedArgumentParameter, self).coerce_value(arg, ba)
        d = self.get_meta(ba).pop_sub()
        if d is None:
            if self.cli.required:
                raise errors.MissingRequiredArguments(self.cli.required)
            args = []
            kwargs = {}
        else:
            args = d.args
            kwargs = d.kwargs
        return self.decorator(val, *args, **kwargs)

    def __str__(self):
        pstr = super(DecoratedArgumentParameter, self).__str__()
        decos = ' '.join(
            str(p) for p in self.cli.parameters.values()
            if not p.undocumented
            )
        if not decos:
            if self.sub_required:
                return pstr
            return '[{0}]'.format(pstr)
        elif self.sub_required:
            return '{0} {1}'.format(decos, pstr)
        else:
            return '[{0} {1}]'.format(decos, pstr)

    def read_argument(self, ba, i):
        super(DecoratedArgumentParameter, self).read_argument(
            self.get_meta(ba).get_deriv(), i)

    def apply_generic_flags(self, ba):
        super(DecoratedArgumentParameter, self).apply_generic_flags(
            self.get_meta(ba).get_deriv())

    def unsatisfied(self, ba):
        m = self.get_meta(ba)
        if m.sub is not None:
            raise errors.MissingRequiredArguments((self,))
        if m.get_deriv().unsatisfied:
            return super(DecoratedArgumentParameter, self).unsatisfied(ba)
        else:
            return False

    def prepare_help(self, helper):
        from clize import help # prevent circular import
        for p in self.cli.parameters.values():
            if not p.undocumented:
                helper.sections[help.LABEL_OPT][p.argument_name] = (p, '')
        doc = inspect.getdoc(self.decorator)
        if doc:
            helper.parse_docstring(
                doc.format(
                    param=self,
                    pname=self.display_name
                ))
        for p in self.cli.parameters.values():
            p.prepare_help(helper)


def argument_decorator(f):
    """Decorates a function to create an annotation for adding parameters
    to qualify another.

    .. literalinclude:: /../examples/argdeco.py
       :lines: 5-24
    """
    return parser.use_mixin(
        DecoratedArgumentParameter, kwargs={'decorator': f})


class InserterParameter(parser.ParameterWithSourceEquivalent):
    """Parameter that provides an argument to the called function without
    requiring an argument on the command line."""

    def __init__(self, value_factory,
                 undocumented, default, conv, aliases=None,
                 display_name='constant_parameter',
                 **kwargs):
        super(InserterParameter, self).__init__(
            undocumented=True, display_name=display_name, **kwargs)
        self.required = True
        self.value_factory = value_factory


class InserterPositionalParameter(InserterParameter):
    def read_argument(self, ba, i):
        ba.args.append(self.value_factory(ba))
        # Get the next pos parameter to process this argument
        try:
            param = next(ba.posparam)
        except StopIteration:
            raise errors.TooManyArguments(ba.in_args[i])
        with errors.SetArgumentErrorContext(param=param):
            param.read_argument(ba, i)
            param.apply_generic_flags(ba)

    def unsatisfied(self, ba):
        ba.args.append(self.value_factory(ba))


class InserterNamedParameter(InserterParameter):
    def unsatisfied(self, ba):
        ba.kwargs[self.argument_name] = self.value_factory(ba)


def value_inserter(value_factory):
    """Create an annotation that hides a parameter from the command-line
    and always gives it the result of a function.

    :param function value_factory: Called to determine the value to provide
        for the parameter. The current `.parser.CliBoundArguments` instance
        is passed as argument, ie. ``value_factory(ba)``.
    """
    try:
        name = value_factory.__name__
    except AttributeError:
        name = repr(value_factory)
    uc = parser.use_class(
        pos=InserterPositionalParameter, named=InserterNamedParameter,
        kwargs={'value_factory': value_factory},
        name='value_inserter({})'.format(name))
    update_wrapper(uc, value_factory)
    return uc


@value_inserter
def pass_name(ba):
    """Parameters decorated with this will receive the executable name as
    argument.

    This can be either the path to a Python file, or ``python -m some.module``.    It is also appended with sub-command names.
    """
    return ba.name

