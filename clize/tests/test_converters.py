# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.
import unittest
from datetime import datetime
import tempfile
import shutil
import os
import stat
import sys
from io import StringIO

from sigtools import support, modifiers

from clize import parser, errors, converters, Parameter
from clize.tests.util import Fixtures, SignatureFixtures, Tests


class ConverterRepTests(SignatureFixtures):
    def _test(self, conv, rep, *, make_signature):
        sig = make_signature('*, par: c', globals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(str(csig), rep)

    datetime = converters.datetime, '--par=TIME'
    file = converters.file(), '--par=FILE'


class ConverterTests(SignatureFixtures):
    def _test(self, conv, inp, out, *, make_signature):
        sig = make_signature('*, par: c', globals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        ba = self.read_arguments(csig, ['--par', inp])
        self.assertEqual(out, ba.kwargs['par'])

    dt_jan1 = (
        converters.datetime, '2014-01-01 12:00', datetime(2014, 1, 1, 12, 0))


skip_if_windows = unittest.skipIf(sys.platform.startswith("win"), "Unsupported on Windows")


class FileConverterTests(Tests):
    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.completed = False

    def tearDown(self):
        def set_writable_and_retry(func, path, excinfo):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        shutil.rmtree(self.temp, set_writable_and_retry)

    def run_conv(self, conv, path):
        sig = support.s('*, par: c', globals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        ba = self.read_arguments(csig, ['--par', path])
        return ba.kwargs['par']

    def test_ret_type(self):
        path = os.path.join(self.temp, 'afile')
        arg = self.run_conv(converters.file(mode='w'), path)
        self.assertTrue(isinstance(arg, converters._FileOpener))
        type(arg).__enter__

    def test_file_read(self):
        path = os.path.join(self.temp, 'afile')
        open(path, 'w').close()
        @modifiers.annotate(afile=converters.file())
        def func(afile):
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'r')
            self.assertTrue(f.closed)
            self.completed = True
        o, e = self.crun(func, ['test', path])
        self.assertFalse(o.getvalue())
        self.assertFalse(e.getvalue())
        self.assertTrue(self.completed)

    def test_not_called(self):
        path = os.path.join(self.temp, 'afile')
        open(path, 'w').close()
        @modifiers.annotate(afile=converters.file)
        def func(afile):
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'r')
            self.assertTrue(f.closed)
            self.completed = True
        o, e = self.crun(func, ['test', path])
        self.assertFalse(o.getvalue())
        self.assertFalse(e.getvalue())
        self.assertTrue(self.completed)

    def test_file_write(self):
        path = os.path.join(self.temp, 'afile')
        @modifiers.annotate(afile=converters.file(mode='w'))
        def func(afile):
            self.assertFalse(os.path.exists(path))
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'w')
            self.assertTrue(f.closed)
            self.assertTrue(os.path.exists(path))
            self.completed = True
        o, e = self.crun(func, ['test', path])
        self.assertFalse(o.getvalue())
        self.assertFalse(e.getvalue())
        self.assertTrue(self.completed)

    def test_file_missing(self):
        path = os.path.join(self.temp, 'afile')
        self.assertRaises(errors.BadArgumentFormat,
                          self.run_conv, converters.file(), path)
        @modifiers.annotate(afile=converters.file())
        def func(afile):
            raise NotImplementedError
        stdout, stderr = self.crun(func, ['test', path])
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue().startswith(
            'test: Bad value for afile: File does not exist: '))

    def test_dir_missing(self):
        path = os.path.join(self.temp, 'adir/afile')
        self.assertRaises(errors.BadArgumentFormat,
                          self.run_conv, converters.file(mode='w'), path)
        @modifiers.annotate(afile=converters.file(mode='w'))
        def func(afile):
            raise NotImplementedError
        stdout, stderr = self.crun(func, ['test', path])
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue().startswith(
            'test: Bad value for afile: Directory does not exist: '))

    def test_current_dir(self):
        path = 'afile'
        @modifiers.annotate(afile=converters.file(mode='w'))
        def func(afile):
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'w')
            self.assertTrue(f.closed)
            self.assertTrue(os.path.exists(path))
            self.completed = True
        with self.cd(self.temp):
            stdout, stderr = self.crun(func, ['test', path])
            self.assertFalse(stdout.getvalue())
            self.assertFalse(stderr.getvalue())
        self.assertTrue(self.completed)

    def test_deprecated_default_value(self):
        path = os.path.join(self.temp, 'default')
        open(path, 'w').close()
        def func(afile: converters.file()=path):
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'r')
            self.assertTrue(f.closed)
            self.completed = True
        with self.assertWarns(DeprecationWarning):
            stdout, stderr = self.crun(func, ['test'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertTrue(self.completed)

    def test_cli_default_value(self):
        path = os.path.join(self.temp, 'default')
        open(path, 'w').close()
        def func(afile: (converters.file(), Parameter.cli_default(path))):
            with afile as f:
                self.assertEqual(f.name, path)
                self.assertEqual(f.mode, 'r')
            self.assertTrue(f.closed)
            self.completed = True
        stdout, stderr = self.crun(func, ['test'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertTrue(self.completed)

    def test_default_none_value(self):
        def func(afile: converters.file() = None):
            self.assertIs(afile, None)
            self.completed = True
        stdout, stderr = self.crun(func, ['test'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        self.assertTrue(self.completed)

    def test_noperm_file_write(self):
        path = os.path.join(self.temp, 'afile')
        open(path, mode='w').close()
        os.chmod(path, stat.S_IRUSR)
        self.assertRaises(errors.BadArgumentFormat,
                          self.run_conv, converters.file(mode='w'), path)

    @skip_if_windows
    def test_noperm_dir(self):
        dpath = os.path.join(self.temp, 'adir')
        path = os.path.join(self.temp, 'adir/afile')
        os.mkdir(dpath)
        os.chmod(dpath, stat.S_IRUSR)
        self.assertRaises(errors.BadArgumentFormat,
                          self.run_conv, converters.file(mode='w'), path)

    def test_race(self):
        path = os.path.join(self.temp, 'afile')
        open(path, mode='w').close()
        @modifiers.annotate(afile=converters.file(mode='w'))
        def func(afile):
            os.chmod(path, stat.S_IRUSR)
            with afile:
                raise NotImplementedError
        stdout, stderr = self.crun(func, ['test', path])
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue().startswith(
            'test: Permission denied: '))

    def test_stdin(self):
        stdin = StringIO()
        @modifiers.annotate(afile=converters.file())
        def func(afile):
            with afile as f:
                self.assertIs(f, stdin)
        stdout, stderr = self.crun(func, ['test', '-'], stdin=stdin)
        self.assertTrue(stdin.closed)
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())

    def test_stdout(self):
        @modifiers.annotate(afile=converters.file(mode='w'))
        def func(afile):
            with afile as f:
                self.assertIs(f, sys.stdout)
        stdout, stderr = self.crun(func, ['test', '-'])
        self.assertTrue(stdout.closed)
        self.assertFalse(stderr.getvalue())

    def test_change_sym(self):
        @modifiers.annotate(afile=converters.file(stdio='gimmestdio'))
        def func(afile):
            with afile as f:
                self.assertIs(f, sys.stdin)
        stdout, stderr = self.crun(func, ['test', 'gimmestdio'])
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())
        with self.cd(self.temp):
            self.assertFalse(os.path.exists('-'))
            stdout, stderr = self.crun(func, ['test', '-'])
            self.assertFalse(stdout.getvalue())
            self.assertTrue(stderr.getvalue().startswith(
                'test: Bad value for afile: File does not exist: '))

    def test_no_sym(self):
        @modifiers.annotate(afile=converters.file(stdio=None))
        def func(afile):
            raise NotImplementedError
        self.assertFalse(os.path.exists('-'))
        stdout, stderr = self.crun(func, ['test', '-'])
        self.assertFalse(stdout.getvalue())
        self.assertTrue(stderr.getvalue().startswith(
            'test: Bad value for afile: File does not exist: '))

    def test_stdin_no_close(self):
        stdin = StringIO()
        @modifiers.annotate(afile=converters.file(keep_stdio_open=True))
        def func(afile):
            with afile as f:
                self.assertIs(f, stdin)
        stdout, stderr = self.crun(func, ['test', '-'], stdin=stdin)
        self.assertFalse(stdin.closed)
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())

    def test_stdout_no_close(self):
        @modifiers.annotate(afile=converters.file(mode='w', keep_stdio_open=True))
        def func(afile):
            with afile as f:
                self.assertIs(f, sys.stdout)
        stdout, stderr = self.crun(func, ['test', '-'])
        self.assertFalse(stdout.closed)
        self.assertFalse(stdout.getvalue())
        self.assertFalse(stderr.getvalue())


class ConverterErrorTests(Fixtures):
    def _test(self, conv, inp):
        sig = support.s('*, par: c', globals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertRaises(errors.BadArgumentFormat,
                          self.read_arguments, csig, ['--par', inp])

    dt_baddate = converters.datetime, 'not a date'
