# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import __future__
import os
import sys
import inspect
import unittest
from contextlib import contextmanager
from io import StringIO

import repeated_test
from sigtools import support

from clize import runner


class Tests(unittest.TestCase):
    maxDiff = 5000

    def read_arguments(self, sig, args):
        return sig.read_arguments(args, 'test')

    def crun(self, func, args, stdin=None, **kwargs):
        orig = sys.stdin, sys.stdout, sys.stderr
        if stdin is None:
            stdin = StringIO()
        sys.stdin = stdin
        sys.stdout = stdout = StringIO()
        sys.stderr = stderr = StringIO()
        try:
            runner.run(func, args=args, exit=False, out=stdout, err=stderr, **kwargs)
            return stdout, stderr
        finally:
            sys.stdin, sys.stdout, sys.stderr = orig

    @contextmanager
    def cd(self, directory):
        cwd = os.getcwd()
        try:
            os.chdir(directory)
            yield
        finally:
            os.chdir(cwd)

    def assertLinesEqual(self, expected, actual):
        exp_split = list(filter(None,
            (line.rstrip() for line in inspect.cleandoc(expected).split('\n'))))
        act_split = list(filter(None,
            (line.rstrip() for line in actual.split('\n'))))
        self.assertEqual(exp_split, act_split)

    @contextmanager
    def maybe_expect_warning(self, maybe_warning):
        if maybe_warning is not None:
            with self.assertWarns(maybe_warning) as warn_context:
                yield warn_context
        else:
            yield None




support_s_without_annotations_feature = repeated_test.NamedAlternative("no __future__ features", support.s)
@repeated_test.NamedAlternative("with __future__.annotations")
def support_s_with_annotations_feature(*args, future_features=(), **kwargs):
    return support.s(*args, future_features=future_features + ("annotations",), **kwargs)


support_f_without_annotations_feature = repeated_test.NamedAlternative("no __future__ features", support.f)
@repeated_test.NamedAlternative("with __future__.annotations")
def support_f_with_annotations_feature(*args, future_features=(), **kwargs):
    return support.f(*args, future_features=future_features + ("annotations",), **kwargs)


has_future_annotations = (
    hasattr(__future__, "annotations")
)


Fixtures = repeated_test.WithTestClass(Tests)
tup = repeated_test.tup

@repeated_test.with_options_matrix(
    make_signature =
        [support_s_without_annotations_feature, support_s_with_annotations_feature]
        if has_future_annotations else
        [support_s_without_annotations_feature]
)
class SignatureFixtures(Fixtures):
    _test = None


@repeated_test.with_options_matrix(
    make_function =
        [support_f_without_annotations_feature, support_f_with_annotations_feature]
        if has_future_annotations else
        [support_f_without_annotations_feature]
)
class FunctionFixtures(Fixtures):
    _test = None


class Matching(object):
    def __init__(self, condition):
        self.condition = condition

    def __eq__(self, other):
        return self.condition(other)


@Matching
def any(other):
    return True


def any_instance_of(cls):
    @Matching
    def condition(obj):
        return isinstance(obj, cls)
    return condition
