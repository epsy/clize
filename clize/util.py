# clize -- A command-line argument parser for Python
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

"""various"""

import os
from functools import update_wrapper

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import six


class _Unset(object):
    __slots__ = ()
    def __repr__(self):
        return '<unset>'
UNSET = _Unset()
del _Unset

def identity(x=None):
    return x

def name_py2cli(name, kw=False):
    name = name.strip('_').replace('_', '-')
    if kw:
        if len(name) > 1:
            return '--' + name
        else:
            return '-' + name
    else:
        return name

def name_cli2py(name, kw=False):
    return name.strip('-').replace('-', '_')

def name_type2cli(typ):
    if typ is identity or typ in six.string_types:
        return 'STR'
    else:
        return typ.__name__.upper()

def maybe_iter(x):
    try:
        iter(x)
    except TypeError:
        return x,
    else:
        if isinstance(x, six.string_types):
            return x,
    return x

def dict_from_names(obj, receiver=None, func=identity):
    try:
        obj.items
    except AttributeError:
        pass
    else:
        if receiver is None:
            return obj
        else:
            receiver.update(obj)
            return receiver
    if receiver is None:
        receiver = OrderedDict()
    receiver.update((func(x.__name__), x) for x in maybe_iter(obj))
    return receiver

class property_once(object):
    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func
        self.key = func.__name__

    def __get__(self, obj, owner):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.key] # could happen if we've been
                                          # assigned to multiple names
        except KeyError:
            ret = obj.__dict__[self.key] = self.func(obj)
            return ret

    def __repr__(self):
        return '<property_once from {0!r}>'.format(self.func)


class _FormatterRow(object):
    def __init__(self, columns, cells):
        self.columns = columns
        self.cells = cells

    def __iter__(self):
        return iter(self.cells)

    def __repr__(self):
        return repr(self.cells)

    def __str__(self):
        return self.columns.format_cells(self.cells)

class _FormatterColumns(object):
    def __init__(self, formatter, num, spacing, align,
                 min_widths, max_widths):
        self.formatter = formatter
        self.num = num
        self.spacing = spacing
        self.align = align or '<' * num
        self.min_widths = min_widths or (0,) * num
        self.max_widths = max_widths or (None,) * num
        self.rows = []
        self.finished = False

    def __enter__(self):
        return self

    def append(self, *cells):
        if len(cells) != self.num:
            raise ValueError('expected {0} cells but got {1}'.format(
                             self.num, len(cells)))
        row = _FormatterRow(self, cells)
        self.rows.append(row)
        self.formatter.append(row)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finished = True
        self.compute_widths()

    def compute_widths(self):
        self.widths = tuple(
            max(len(s) for s in col)
            for col in zip(*self.rows)
            )

    def format_cells(self, cells):
        return self.spacing.join(
            '{0:{1}{2}}'.format(cell, align, width)
            for cell, align, width in zip(cells, self.align, self.widths)
            )

class _FormatterIndent(object):
    def __init__(self, formatter, indent):
        self.formatter = formatter
        self.indent = indent

    def __enter__(self):
        self.formatter._indent += self.indent
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.formatter._indent -= self.indent

try:
    terminal_width = max(50, os.get_terminal_size().columns - 1)
except (AttributeError, OSError):
    terminal_width = 70 #fair terminal dice roll

class Formatter(object):
    delimiter = '\n'

    def __init__(self, max_width=-1):
        self.max_width = terminal_width if max_width == -1 else max_width
        self.lines = []
        self._indent = 0

    def append(self, line, indent=0):
        self.lines.append((self._indent + indent, line))

    def new_paragraph(self):
        if self.lines and self.lines[-1][1]:
            self.lines.append((0, ''))

    def extend(self, iterable):
        if not isinstance(iterable, Formatter):
            iterator = ((0, line) for line in iterable)
        else:
            iterator = iter(iterable)
        try:
            first = next(iterator)
        except StopIteration:
            return
        if not first[1]:
            self.new_paragraph()
        else:
            self.append(first[1], first[0])
        for indent, line in iterator:
            self.append(line, indent)

    def indent(self, indent=2):
        return _FormatterIndent(self, indent)

    def columns(self, num=2, spacing='   ', align=None,
                min_widths=None, max_widths=None):
        return _FormatterColumns(
            self, num, spacing, align,
            min_widths, max_widths)

    def __str__(self):
        if self.lines and not self.lines[-1][1]:
            lines = self.lines[:-1]
        else:
            lines = self.lines
        return self.delimiter.join(
            ' ' * indent + six.text_type(line)
            for indent, line in lines
            )

    def __iter__(self):
        return iter(self.lines)

