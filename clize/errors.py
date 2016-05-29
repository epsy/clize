# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from functools import partial


class UserError(ValueError):
    """An error to be printed to the user."""

    def __str__(self):
        return self.prefix_with_pname(super(UserError, self).__str__())

    def prefix_with_pname(self, message):
        return '{0}: {1}'.format(self.get_pname('Error'), message)

    def get_pname(self, default='command'):
        try:
            return self.pname
        except AttributeError:
            return default


class ArgumentError(UserError):
    """An error related to the arguments passed through the command-line
    interface"""
    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __str__(self):
        usage = ''
        try:
            usage = '\n' + '\n'.join(
                self.cli.helper.show_usage(self.get_pname()))
        except Exception:
            pass
        return self.prefix_with_pname(self.message + usage)


class MissingRequiredArguments(ArgumentError):
    """Raised when required parameters have not been provided an argument"""

    def __init__(self, missing):
        self.missing = missing

    @property
    def message(self):
        return "Missing required arguments: {0}".format(
                    ', '.join(arg.display_name for arg in self.missing))


class TooManyArguments(ArgumentError):
    """Raised when too many positional arguments have been passed for the
    parameters to consume."""

    def __init__(self, extra):
        self.extra = extra

    @property
    def message(self):
        return "Received extra arguments: {0}".format(
                    ' '.join(self.extra))


class DuplicateNamedArgument(ArgumentError):
    """Raised when a named option or flag has been passed twice."""

    @property
    def message(self):
        return "{0} was specified more than once".format(
            self.param.aliases[0])


class UnknownOption(ArgumentError):
    """Raised when a named argument has no matching parameter."""

    def __init__(self, name):
        self.name = name

    @property
    def message(self):
        best_guess = None
        if self.ba:
            best_guess = self.ba.get_best_guess(self.name)
        if best_guess:
            return "Unknown option {0!r}. Did you mean {1!r}?" \
                .format(self.name, best_guess)
        else:
            return "Unknown option {0!r}".format(self.name)


class MissingValue(ArgumentError):
    """Raised when an option received no value."""

    @property
    def message(self):
        return "No value found after {0}".format(self.param.display_name)


class NotEnoughValues(ArgumentError):
    """Raised when MultiOptionParameter is given less values than its min
    parameter."""

    @property
    def message(self):
        return "Received too few values for {0.display_name}".format(
                self.param)


class TooManyValues(ArgumentError):
    """Raised when MultiOptionParameter is given more values than its max
    parameter."""

    @property
    def message(self):
        return "Received too many values for {0.display_name}".format(
                self.param)


class CliValueError(ValueError):
    """Specialization of `ValueError` for showing a message to the user along
    with the error rather than just the incorrect value."""

class BadArgumentFormat(ArgumentError):
    """Raised when an argument cannot be converted to the correct format."""

    def __init__(self, text):
        self.text = text

    @property
    def message(self):
        return "Bad value for {0.display_name}: {1}".format(
            self.param, self.text)


class ArgsBeforeAlternateCommand(ArgumentError):
    """Raised when there are arguments before a non-fallback alternate
    command."""
    def __init__(self, param):
        self.param = param

    @property
    def message(self):
        return "Arguments found before alternate action parameter {0}".format(
            self.param.display_name)


class SetErrorContext(object):
    """Context manager that sets attributes on exceptions that are raised
    past it"""

    def __init__(self, exc_type, **attributes):
        """
        :param exc_type: The exception type to operate on.
        :param attributes: The attributes to set on the matching exceptions.
            They will only be set if yet unset on the exception.
        """
        self.exc_type = exc_type
        self.values = attributes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, self.exc_type):
            for key, val in self.values.items():
                if not hasattr(exc_val, key):
                    setattr(exc_val, key, val)

SetUserErrorContext = partial(SetErrorContext, UserError)
SetArgumentErrorContext = partial(SetErrorContext, ArgumentError)
