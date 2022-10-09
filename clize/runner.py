# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.
import contextlib
import pathlib
import sys
import os
import typing
import warnings
from functools import partial, update_wrapper
import itertools
import shutil

from sigtools.modifiers import annotate, autokwoargs, kwoargs
from sigtools.specifiers import forwards_to_method, signature

from clize import util, errors, parser, parameters


class _BasicHelper(object):
    def __init__(self, description, usages):
        if description is not None:
            self.description = description
        if usages is not None:
            def _usages():
                return usages
            self.usages = _usages

class _CliWrapper(object):
    def __init__(self, obj, description, usages):
        update_wrapper(self, obj)
        if description is not None or usages is not None:
            obj.helper = _BasicHelper(description, usages)
        self.cli = obj

def cli_commands(obj, namef, clizer):
    cmds = util.OrderedDict()
    try:
        names = util.dict_from_names(obj).items()
    except AttributeError:
        raise ValueError("Cannot guess name for anonymous objects "
                         "(lists, dicts, etc)")
    func_to_names = util.OrderedDict()
    for key, val in names:
        if not key:
            continue
        names = tuple(namef(name) for name in util.maybe_iter(key))
        cli = clizer.get_cli(val)
        for name in names:
            func_to_names.setdefault(cli, []).append(name)
    cmds = util.OrderedDict((tuple(names), cli) for cli, names in func_to_names.items())
    cmd_by_name = {name: cli for names, cli in cmds.items() for name in names}
    return cmds, cmd_by_name

class Clize(object):
    """Wraps a function into a CLI object that accepts command-line arguments
    and translates them to match the wrapped function's parameters."""

    @forwards_to_method('__init__', 1)
    def __new__(cls, fn=None, **kwargs):
        if fn is None:
            return partial(cls, **kwargs)
        else:
            return super(Clize, cls).__new__(cls)

    def __init__(self, fn, owner=None, alt=(), extra=(),
                 help_names=('help', 'h'), helper_class=None, hide_help=False):
        """
        :param sequence alt: Alternate actions the CLI will handle.
        :param help_names: Names to use to trigger the help.
        :type help_names: sequence of strings
        :param helper_class: A callable to produce a helper object to be
            used when the help is triggered. If unset, uses `.ClizeHelp`.
        :type helper_class: a type like `.ClizeHelp`
        :param bool hide_help: Mark the parameters used to trigger the help
            as undocumented.
        """
        update_wrapper(self, fn)
        self.func = fn
        self.owner = owner
        self.alt = util.maybe_iter(alt)
        self.extra = extra
        self.help_names = help_names
        self.help_aliases = [util.name_py2cli(s, kw=True) for s in help_names]
        self.helper_class = helper_class
        self.hide_help = hide_help

    def __class_getitem__(cls, item):
        return parser.ClizeAnnotations(item)

    def parameters(self):
        """Returns the parameters used to instantiate this class, minus the
        wrapped callable."""
        return {
            'owner': self.owner,
            'alt': self.alt,
            'help_names': self.help_names,
            'helper_class': self.helper_class,
            'hide_help': self.hide_help,
            }

    def _key(self):
        return (
            self.func,
            self.owner,
            tuple(self.alt),
            tuple(self.extra),
            tuple(self.help_names),
            tuple(self.help_aliases),
            self.helper_class,
            self.hide_help,
        )

    def __eq__(self, other):
        return type(self) is type(other) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    @classmethod
    def keep(cls, fn=None, **kwargs):
        """Instead of wrapping the decorated callable, sets its ``cli``
        attribute to a `.Clize` instance. Useful if you need to use the
        decorator but must still be able to call the function regularly.
        """
        if fn is None:
            return partial(cls.keep, **kwargs)
        else:
            fn.cli = cls(fn, **kwargs)
            return fn

    @classmethod
    @kwoargs(start='description')
    def as_is(cls, obj=None, description=None, usages=None):
        """Returns a CLI object which uses the given callable with no
        translation.

        The following parameters improve the decorated object's compatibility
        with Clize's help output:

        :param description: A description for the command.
        :param usages: A list of usages for the command.

        .. seealso:: :ref:`interop`
        """
        if obj is None:
            return partial(cls.as_is, description=description, usages=usages)
        return _CliWrapper(obj, description, usages)

    @classmethod
    def get_cli(cls, obj, **kwargs):
        """Makes an attempt to discover a command-line interface for the
        given object.

        .. _cli-object:

        The process used is as follows:

        1. If the object has a ``cli`` attribute, it is used with no further
           transformation.
        2. If the object is callable, `.Clize` or whichever object this
           class method is used from is used to build a CLI. ``**kwargs`` are
           forwarded to its initializer.
        3. If the object is iterable, `.SubcommandDispatcher` is used on
           the object, and its `cli <.SubcommandDispatcher.cli>` method
           is used.

        Most notably, `clize.run` uses this class method in order to interpret
        the given object(s).
        """
        try:
            cli = obj.cli
        except AttributeError:
            if callable(obj):
                cli = cls(obj, **kwargs)
            else:
                try:
                    iter(obj)
                except TypeError:
                    raise TypeError("Don't know how to build a cli for "
                                    + repr(obj))
                cli = SubcommandDispatcher(obj, **kwargs).cli
        return cli

    @property
    def cli(self):
        """Returns the object itself, in order to be selected by `.get_cli`"""
        return self

    def __repr__(self):
        return '<Clize for {0!r}>'.format(self.func)

    def __get__(self, obj, owner=None):
        try:
            func = self.func.__get__(obj, owner)
        except AttributeError:
            func = self.func
        if func is self.func:
            return self
        params = self.parameters()
        params['owner'] = obj
        return type(self)(func, **params)

    @util.property_once
    def helper(self):
        """A cli object(usually inherited from `.help.Help`) when the user
        requests a help message. See the constructor for ways to affect this
        attribute."""
        if self.helper_class is None:
            from clize.help import ClizeHelp as class_
        else:
            class_ = self.helper_class
        return class_(self, self.owner)

    @util.property_once
    def signature(self):
        """The `.parser.CliSignature` object used to parse arguments."""
        extra = itertools.chain(self._process_alt(self.alt), self.extra)
        with self._move_warnings_to_func():
            return parser.CliSignature.from_signature(
                self.func_signature,
                extra=extra)

    @util.property_once
    def func_signature(self):
        return signature(self.func)

    @contextlib.contextmanager
    def _move_warnings_to_func(self):
        try:
            code = self.func.__code__
            filename = code.co_filename
            lineno = code.co_firstlineno
            module = self.func.__module__
            module_globals = self.func.__globals__
        except AttributeError:
            yield
        else:
            with warnings.catch_warnings(record=True) as caught_warnings:
                yield
            for warning in caught_warnings:
                registry = module_globals.setdefault("__warningregistry__", {})
                warnings.warn_explicit(warning.message, warning.category, filename, lineno, module, registry, module_globals)

    def _process_alt(self, alt):
        if self.help_names:
            p = parser.FallbackCommandParameter(
                func=self.helper.cli, undocumented=self.hide_help,
                aliases=self.help_aliases)
            yield p

        for name, func in util.dict_from_names(alt).items():
            func = self.get_cli(func)
            param = parser.AlternateCommandParameter(
                undocumented=False, func=func,
                aliases=[util.name_py2cli(name, kw=True)])
            yield param

    def __call__(self, *args):
        with errors.SetUserErrorContext(cli=self, pname=args[0]):
            func, name, posargs, kwargs = self.read_commandline(args)
            return func(*posargs, **kwargs)

    def read_commandline(self, args):
        """Reads the command-line arguments from args and returns a tuple
        with the callable to run, the name of the program, the positional
        and named arguments to pass to the callable.

        :raises: `.ArgumentError`
        """
        ba = self.signature.read_arguments(args[1:], args[0])
        func, post, posargs, kwargs = ba
        name = ' '.join([args[0]] + post)
        return func or self.func, name, posargs, kwargs

def _dispatcher_helper(*args, **kwargs):
    """alias for clize.help.DispatcherHelper, avoiding circular import"""
    from clize.help import ClizeHelp, HelpForSubcommands
    return ClizeHelp(*args, builder=HelpForSubcommands.from_subject, **kwargs)


class SubcommandDispatcher(object):
    clizer = Clize

    def __init__(self, commands=(), description=None, footnotes=None, **kwargs):
        self.cmds, self.cmds_by_name = cli_commands(
            commands, namef=util.name_py2cli, clizer=self.clizer)
        self.description = description
        self.footnotes = footnotes
        self.clize_kwargs = kwargs

    @annotate(name=parameters.pass_name,
              command=parser.Parameter.LAST_OPTION)
    def _cli(self, name, command, *args):
        try:
            func = self.cmds_by_name[command.lower()]
        except KeyError:
            guess = util.closest_option(command, list(self.cmds_by_name))
            if guess:
                raise errors.ArgumentError(
                    'Unknown command "{0}". Did you mean "{1}"?'
                    .format(command, guess))
            raise errors.ArgumentError('Unknown command "{0}"'.format(command))
        return func('{0} {1}'.format(name, command), *args)

    @property
    def cli(self):
        c = Clize(self._cli, helper_class=_dispatcher_helper,
                  **self.clize_kwargs)
        c.owner = self
        return c


def _get_executable(path, *, to_path=pathlib.PurePath, which=shutil.which) -> typing.Union[None, str]:
    """Get the shortest invocation for a given command"""
    if not path:
        return None
    path = to_path(path)
    which_result = which(path.name)
    if which_result and to_path(which_result) == path:
        return path.name
    try:
        rel = path.relative_to(to_path())
    except ValueError:
        return str(path)
    return str(rel)


def main_module_name(module):
    try:
        modname = os.path.splitext(os.path.basename(module.__file__))[0]
        if modname == '__main__':
            return module.__package__
        elif not module.__package__:
            return modname
        else:
            return module.__package__ + '.' + modname
    except AttributeError:
        return None


def _fix_argv(argv, sys_path, main_module, *, platform=sys.platform, executable=sys.executable, get_executable=_get_executable, get_main_module_name=main_module_name):
    """Tries to restore the given sys.argv to something closer to what the user would've typed"""
    if not sys_path[0]:
        name = get_main_module_name(main_module)
        if name is not None:
            argv = argv[:]
            argv[0] = f'{get_executable(executable) or "python"} -m {name}'
    elif platform.startswith("win"):
        argv = argv[:]
        argv[0] = f'{get_executable(executable) or "python"} {argv[0]}'
    else:
        name = get_executable(argv[0])
        argv = argv[:]
        argv[0] = name
    return argv


@autokwoargs
def run(args=None, catch=(), exit=True, out=None, err=None, *fn, **kwargs):
    """Runs a function or :ref:`CLI object<cli-object>` with ``args``, prints
    the return value if not None, or catches the given exception types as well
    as `clize.UserError` and prints their string representation, then exit with
    the appropriate status code.

    :param sequence args: The arguments to pass the CLI, for instance
        ``('./a_script.py', 'spam', 'ham')``. If unspecified, uses `sys.argv`.
    :param catch: Catch these exceptions and print their string representation
        rather than letting Python print an uncaught exception traceback.
    :type catch: sequence of exception classes
    :param bool exit: If true, exit with the appropriate status code once the
        function is done.
    :param file out: The file in which to print the return value of the
        command. If unspecified, uses `sys.stdout`
    :param file err: The file in which to print any exception text.
        If unspecified, uses `sys.stderr`.

    """
    if len(fn) == 1:
        fn = fn[0]
    cli = Clize.get_cli(fn, **kwargs)

    if args is None:
        # import __main__ causes double imports when
        # python2.7 -m apackage
        # is used
        module = sys.modules['__main__']
        args = _fix_argv(sys.argv, sys.path, module)
    if out is None:
        out = sys.stdout
    if err is None:
        err = sys.stderr

    try:
        ret = cli(*args)
    except tuple(catch) + (errors.UserError,) as exc:
        print(str(exc), file=err)
        if exit:
            sys.exit(2 if isinstance(exc, errors.ArgumentError) else 1)
    else:
        if ret is not None:
            print(ret, file=out)
        if exit:
            sys.exit()

