# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

from datetime import datetime
import unittest
import tempfile
import shutil
import os

from sigtools import support

from clize import parser, errors
from clize.extra import converters
from clize.tests import util


@util.repeated_test
class ConverterRepTests(object):
    def _test_func(self, conv, rep):
        sig = support.s('*, par: c', locals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertEqual(str(csig), rep)

    datetime = converters.datetime, '--par=DATETIME'
    file = converters.file(), '--par=FILE'


@util.repeated_test
class ConverterTests(object):
    def _test_func(self, conv, inp, out):
        sig = support.s('*, par: c', locals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        ba = util.read_arguments(csig, ['--par', inp])
        self.assertEqual(out, ba.kwargs['par'])

    dt_jan1 = (
        converters.datetime, '2014-01-01 12:00', datetime(2014, 1, 1, 12, 0))


class FileConverterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp)

    def run_conv(self, conv, path):
        sig = support.s('*, par: c', locals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        ba = util.read_arguments(csig, ['--par', path])
        return ba.kwargs['par']

    def test_file_read(self):
        path = os.path.join(self.temp, 'afile')
        open(path, 'w').close()
        arg = self.run_conv(converters.file(), path)
        self.assertEqual(arg.name, path)
        self.assertEqual(arg.mode, 'r')
        self.assertTrue(arg.closed)

    def test_file_write(self):
        path = os.path.join(self.temp, 'afile')
        arg = self.run_conv(converters.file(mode='w'), path)
        self.assertEqual(arg.name, path)
        self.assertEqual(arg.mode, 'w')
        self.assertTrue(arg.closed)


@util.repeated_test
class ConverterErrorTests(object):
    def _test_func(self, conv, inp):
        sig = support.s('*, par: c', locals={'c': conv})
        csig = parser.CliSignature.from_signature(sig)
        self.assertRaises(errors.BadArgumentFormat,
                          util.read_arguments, csig, ['--par', inp])

    dt_baddate = converters.datetime, 'not a date'
