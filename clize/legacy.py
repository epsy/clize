# clize -- A command-line argument parser for Python
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

import warnings
from functools import partial
from itertools import chain
from collections import defaultdict

from sigtools.specifiers import forwards_to
from sigtools.modifiers import autokwoargs, annotate

from clize import runner, parser, util


def _clize(fn, alias={}, force_positional=(), coerce={},
           require_excess=False, extra=(),
           use_kwoargs=None):
    sig = util.funcsigs.signature(fn)
    has_kwoargs = False
    annotations = defaultdict(list)
    ann_positional = []
    for param in sig.parameters.values():
        if param.kind == param.KEYWORD_ONLY:
            has_kwoargs = True
        elif require_excess and param.kind == param.VAR_POSITIONAL:
            annotations[param.name].append(parser.Parameter.REQUIRED)
        if param.annotation != param.empty:
            ann = util.maybe_iter(param.annotation)
            annotations[param.name].extend(ann)
            if clize.POSITIONAL in ann:
                ann_positional.append(param.name)
                annotations[param.name].remove(clize.POSITIONAL)
    for name, aliases in alias.items():
        annotations[name].extend(aliases)
    for name, func in coerce.items():
        annotations[name].append(func)
    annotate(**annotations)(fn)
    use_kwoargs = has_kwoargs if use_kwoargs is None else use_kwoargs
    if not use_kwoargs:
        fn = autokwoargs(
            exceptions=chain(ann_positional, force_positional))(fn)
    return runner.Clize(fn)


@forwards_to(_clize, 1)
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
