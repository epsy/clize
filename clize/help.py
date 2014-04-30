# clize - automatically generate command-line interfaces from callables
# clize -- A command-line argument parser for Python
# Copyright (C) 2013 by Yann Kaiser <kaiser.yann@gmail.com>
# See COPYING for details.

from __future__ import unicode_literals

import itertools
from functools import partial
import inspect
import re

import six
from sigtools.modifiers import annotate, kwoargs
from sigtools.wrappers import wrappers

from clize import runner, parser, util

def lines_to_paragraphs(L):
    return list(itertools.chain.from_iterable((x, '') for x in L))

p_delim = re.compile(r'\n\s*\n')

class Help(object):

    def __init__(self, subject, owner):
        self.subject = subject
        self.owner = owner

    @util.property_once
    def header(self):
        self.prepare()
        return self.__dict__['header']

    def prepare(self):
        """Override for stuff to be done once per subject"""

    @runner.Clize(pass_name=True, hide_help=True)
    @kwoargs('usage')
    @annotate(args=parser.Parameter.UNDOCUMENTED)
    def cli(self, name, usage=False, *args):
        """Show the help

        usage: Only show the full usage
        """
        name = name.rpartition(' ')[0]
        f = util.Formatter()
        if usage:
            f.extend(self.show_full_usage(name))
        else:
            f.extend(self.show(name))
        return six.text_type(f)

def update_new(target, other):
    for key, val in six.iteritems(other):
        if key not in target:
            target[key] = val

def split_docstring(s):
    if not s:
        return
    code_coming = False
    code = False
    for p in p_delim.split(s):
        if code_coming or code and p.startswith(' '):
            yield p
            code_coming = False
            code = True
        else:
            item = ' '.join(p.split())
            if item.endswith(':'):
                code_coming = True
            code = False
            yield item


class ClizeHelp(Help):
    @property
    def signature(self):
        return self.subject.signature

    @classmethod
    def get_arg_type(cls, arg):
        if arg.kwarg:
            if arg.func:
                return 'alt'
            else:
                return 'opt'
        else:
            return 'pos'

    @classmethod
    def filter_undocumented(cls, params):
        for param in params:
            if not param.undocumented:
                yield param

    def prepare(self):
        self.arguments = {
            'pos': list(self.filter_undocumented(self.signature.positional)),
            'opt': list(self.filter_undocumented(self.signature.named)),
            'alt': list(self.filter_undocumented(self.signature.alternate)),
            }
        self.header, self.arghelp, self.before, self.after, self.footer = \
            self.parse_help()
        self.order = list(self.arghelp.keys())

    def parse_func_help(self, obj):
        return self.parse_docstring(inspect.getdoc(obj))

    argdoc_re = re.compile('^([a-zA-Z_]+): ?(.+)$')
    def parse_docstring(self, s):
        header = []
        arghelp = util.OrderedDict()
        before = {}
        after = {}
        last_arghelp = None
        cur_after = []
        for p in split_docstring(s):
            argdoc = self.argdoc_re.match(p)
            if argdoc:
                argname, text = argdoc.groups()
                arghelp[argname] = text
                if cur_after:
                    prev, this = cur_after, None
                    if prev[-1].endswith(':'):
                        this = [prev.pop()]
                    if last_arghelp:
                        after[last_arghelp] = cur_after
                    else:
                        header.extend(cur_after)
                    if this:
                        before[argname] = this
                    cur_after = []
                last_arghelp = argname
            else:
                cur_after.append(p)
        if not arghelp:
            header = cur_after
            footer = []
        else:
            footer = cur_after
        return (
            lines_to_paragraphs(header), arghelp, before, after,
            lines_to_paragraphs(footer)
            )

    def parse_help(self):
        header, arghelp, before, after, footer = \
            self.parse_func_help(self.subject.func)
        for wrapper in wrappers(self.subject.func):
            _, w_arghelp, w_before, w_after, _ = \
                self.parse_func_help(wrapper)
            update_new(arghelp, w_arghelp)
            update_new(before, w_before)
            update_new(after, w_after)
        return header, arghelp, before, after, footer

    @property
    def description(self):
        try:
            return self.header[0]
        except IndexError:
            return ''

    def show_usage(self, name):
        return 'Usage: {0} {1}{2}'.format(
            name,
            '[OPTIONS] ' if self.signature.named else '',
            ' '.join(str(arg)
                     for arg in self.signature.positional)
            ),

    def alternates_with_helper(self):
        for param in self.signature.alternate:
            if param.undocumented:
                continue
            try:
                helper = param.func.helper
            except AttributeError:
                pass
            else:
                yield param, param.display_name, helper

    def usages(self, name):
        yield name, str(self.signature)
        for param, subname, helper in self.alternates_with_helper():
            for usage in helper.usages(' '.join((name, subname))):
                yield usage

    def show_full_usage(self, name):
        for name, usage in self.usages(name):
            yield ' '.join((name, usage))

    def docstring_index(self, param):
        name = getattr(param, 'argument_name', param.display_name)
        try:
            return self.order.index(name), name
        except ValueError:
            return float('inf'), name

    kind_order = [
        ('pos', 'Positional arguments:'),
        ('opt', 'Options:'),
        ('alt', 'Other actions:'),
        ]
    def show_arguments(self):
        f = util.Formatter()
        with f.columns() as cols:
            for key, message in self.kind_order:
                f.new_paragraph()
                if key in self.arguments and self.arguments[key]:
                    if key == 'opt':
                        params = sorted(self.arguments[key],
                                        key=self.docstring_index)
                    else:
                        params = self.arguments[key]
                    if getattr(params[0], 'argument_name', None
                            ) not in self.before:
                        f.append(message)
                    with f.indent():
                        for arg in params:
                            self.show_argument(arg, f, cols)
        return f

    def show_argument(self, param, f, cols):
        name = getattr(param, 'argument_name', None)
        if name in self.before:
            for p in self.before[name]:
                f.new_paragraph()
                f.append(p, indent=-2)
        desc = getattr(param, 'description', None)
        if desc is None:
            desc = self.arghelp.get(name, '')
        if getattr(param, 'default', None) in (util.UNSET, None, False, ''):
            default = ''
        else:
            default = "((default: {0})".format(param.default)
        cols.append(param.full_name, desc + default)
        if name in self.after:
            for p in self.after[name]:
                f.new_paragraph()
                f.append(p, indent=-2)
            f.new_paragraph()

    def show(self, name):
        f = util.Formatter()
        for iterable in (self.show_usage(name), self.header,
                         self.show_arguments(), self.footer):
            f.extend(iterable)
            f.new_paragraph()
        return f

class DispatcherHelper(Help):
    def show_commands(self):
        f = util.Formatter()
        f.append('Commands:')
        with f.indent():
            with f.columns() as cols:
                for names, command in self.owner.cmds.items():
                    cols.append(', '.join(names), command.helper.description)
        return f

    def prepare_notes(self, doc):
        if doc is None:
            return ()
        else:
            return lines_to_paragraphs(split_docstring(inspect.cleandoc(doc)))

    def prepare(self):
        self.header = self.prepare_notes(self.owner.description)
        self.footer = self.prepare_notes(self.owner.footnotes)

    def show(self, name):
        f = util.Formatter()
        for text in (self.show_usage(name), self.header,
                     self.show_commands(), self.footer):
            f.extend(text)
            f.new_paragraph()
        return f

    def show_usage(self, name):
        yield 'Usage: {0} command [args...]'.format(name)

    def subcommands_with_helper(self):
        for names, subcommand in self.owner.cmds.items():
            try:
                helper = subcommand.helper
            except AttributeError:
                pass
            else:
                yield names, subcommand, helper

    def usages(self, name):
        if self.subject.help_aliases:
            help_name = ' '.join((name, self.subject.help_aliases[0]))
            yield help_name, str(self.cli.signature)
        for names, subcommand, helper in self.subcommands_with_helper():
            for usage in helper.usages(' '.join((name, names[0]))):
                yield usage

    def show_full_usage(self, name):
        for name, usage in self.usages(name):
            yield ' '.join((name, usage))
