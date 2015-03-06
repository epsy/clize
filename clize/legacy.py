# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import warnings
from functools import partial
from itertools import chain
from collections import defaultdict

from sigtools import modifiers, specifiers

from clize import runner, parser, util


def _convert_coerce(func):
    if func not in parser._implicit_converters:
        func = parser.value_converter(func)
    return func

def _clize(fn, alias={}, force_positional=(), coerce={},
           require_excess=False, extra=(),
           use_kwoargs=None):
    sig = specifiers.signature(fn)
    has_kwoargs = False
    annotations = defaultdict(list)
    ann_positional = []
    for param in sig.parameters.values():
        coerce_set = False
        if param.kind == param.KEYWORD_ONLY:
            has_kwoargs = True
        elif require_excess and param.kind == param.VAR_POSITIONAL:
            annotations[param.name].append(parser.Parameter.REQUIRED)
        if param.annotation != param.empty:
            for thing in util.maybe_iter(param.annotation):
                if thing == clize.POSITIONAL:
                    ann_positional.append(param.name)
                    continue
                elif callable(thing):
                    coerce_set = True
                    thing = _convert_coerce(thing)
                annotations[param.name].append(thing)
        try:
            func = coerce[param.name]
        except KeyError:
            pass
        else:
            annotations[param.name].append(_convert_coerce(func))
            coerce_set = True
        annotations[param.name].extend(alias.get(param.name, ()))
        if not coerce_set and param.default != param.empty:
            annotations[param.name].append(
                _convert_coerce(type(param.default)))
    fn = modifiers.annotate(**annotations)(fn)
    use_kwoargs = has_kwoargs if use_kwoargs is None else use_kwoargs
    if not use_kwoargs:
        fn = modifiers.autokwoargs(
            exceptions=chain(ann_positional, force_positional))(fn)
    return runner.Clize(fn, extra=extra)


@specifiers.forwards_to(_clize, 1)
def clize(fn=None, **kwargs):
    """Compatibility with clize<3.0 releases. Decorates a function in order
    to be passed to `clize.run`. See :ref:`porting-2`."""
    warnings.warn('Use clize.Clize instead of clize.clize, or pass the '
                  'function directly to run(), undecorated.',
                  DeprecationWarning, stacklevel=2)
    if fn is None:
        return partial(_clize, **kwargs)
    else:
        return _clize(fn, **kwargs)

clize.kwo = partial(clize, use_kwoargs=True)
clize.POSITIONAL = clize.P = parser.ParameterFlag('POSITIONAL',
                                                  'clize.legacy.clize')


class MakeflagParameter(parser.NamedParameter):
    """Parameter class that imitates those returned by Clize 2's `make_flag`
    when passed a callable for source. See :ref:`porting-2`."""
    def __init__(self, func, **kwargs):
        super(MakeflagParameter, self).__init__(**kwargs)
        self.func = func

    def noop(self, *args, **kwargs):
        pass

    def read_argument(self, ba, i):
        # try:
        #     val = ba.in_args[i + 1]
        #     ba.skip = 1
        # except IndexError:
        val = True
        ret = self.func(name=ba.name, command=ba.sig,
                        val=val, params=ba.kwargs)
        if ret:
            ba.func = self.noop


def make_flag(source, names, default=False, type=bool,
              help='', takes_argument=0):
    """Compatibility with clize<3.0 releases. Creates a parameter instance.
    See :ref:`porting-2`."""
    warnings.warn('Compatibility with clize<3.0 releases. Helper function to '
                  'create alternate actions. See :ref:`porting-2`.',
                  DeprecationWarning, stacklevel=1)
    kwargs = {}
    kwargs['aliases'] = [util.name_py2cli(alias, kw=True)
                         for alias in names]
    if callable(source):
        return MakeflagParameter(source, **kwargs)
    cls = parser.OptionParameter
    kwargs['argument_name'] = source
    kwargs['default'] = default
    if not takes_argument:
        return parser.FlagParameter(value=True, **kwargs)
    kwargs['typ'] = type
    if type is int:
        cls = parser.IntOptionParameter
    return cls(**kwargs)
