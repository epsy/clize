# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import six
from sigtools import modifiers

from clize import parser, errors, util


class _ShowList(BaseException):
    pass


class _DummyType(object):
    def __init__(self, name):
        self.clize_type_name = name


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
                    raise ValueError('Duplicate key when uncased')
                used.add(name_)
                yield name_, target

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
            for target, names, _ in self.values
            for name in names)

    def coerce_value(self, value):
        table = self.values_table
        key = value if self.case_sensitive else value.lower()
        if key == self.list_name:
            raise _ShowList
        try:
            return table[key]
        except KeyError:
            raise errors.BadArgumentFormat(
                _DummyType(repr(self.display_name)), value)

    def read_argument(self, ba, i):
        try:
            super(MappedParameter, self).read_argument(ba, i)
        except _ShowList:
            ba.args[:] = []
            ba.kwargs.clear()
            ba.func = self.show_list
            ba.sticky = parser.IgnoreAllOptionParameterArguments(self)

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


@modifiers.autokwoargs
def mapped(values, list_name='list', case_sensitive=None):
    """Creates an annotation for parameters that maps input values to python
    objects.

    :param sequence values: A sequence of ``pyobj, names, description`` tuples.
        For each item, the user can specify a name from ``names`` and the
        parameter will receive the corresponding ``pyobj`` value.
        ``description`` is used when listing the possible values.
    :param str list_name: The value the user can use to show a list of possible
        values and their description.
    :param bool case_sensitive: Force case-sensitiveness for the input values.
        The default is to guess based on the contents of values.

    .. literalinclude:: /../examples/extra/mapped.py
        :lines: 5-19

    """
    return parser.use_mixin(MappedParameter, kwargs={
        'case_sensitive': case_sensitive,
        'list_name': list_name,
        'values': values,
    })


def _conv_oneof(values):
    for value in values:
        if isinstance(value, six.string_types):
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


class NotEnoughValues(errors.ArgumentError):
    """Raised when MultiOptionParameter is given less values than its min
    parameter."""

    @property
    def message(self):
        return "Received too few values for {0.display_name}".format(
                self.param)


class TooManyValues(errors.ArgumentError):
    """Raised when MultiOptionParameter is given more values than its max
    parameter."""

    @property
    def message(self):
        return "Received too many values for {0.display_name}".format(
                self.param)


class MultiOptionParameter(parser.MultiParameter, parser.OptionParameter):
    """Named parameter that can collect multiple values."""

    required = True

    def __init__(self, min, max, **kwargs):
        super(MultiOptionParameter, self).__init__(**kwargs)
        self.min = min
        self.max = max

    def read_argument(self, ba, i):
        val = self.coerce_value(self.get_value(ba, i))
        col = self.get_collection(ba)
        col.append(val)
        if self.min <= len(col):
            ba.unsatisfied.discard(self)
        if self.max is not None and self.max < len(col):
            raise TooManyValues

    def get_collection(self, ba):
        return ba.kwargs.setdefault(self.argument_name, [])

    def apply_generic_flags(self, ba):
        if self.last_option:
            ba.posarg_only = True

    def unsatisfied(self, ba):
        if not self.min:
            ba.kwargs[self.argument_name] = []
            return False
        if not ba.kwargs.get(self.argument_name):
            return True
        raise NotEnoughValues


def multi(min=0, max=None):
    return parser.use_class(named=MultiOptionParameter, kwargs={
            'min': min,
            'max': max,
        })
