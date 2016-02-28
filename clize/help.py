# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2015 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from __future__ import unicode_literals

import itertools
import inspect
import re

import six
from sigtools.modifiers import annotate, kwoargs
from sigtools.wrappers import wrappers

from clize import runner, parser, util, parameters

def lines_to_paragraphs(L):
    return list(itertools.chain.from_iterable((x, '') for x in L))

p_delim = re.compile(r'\n\s*\n')

class Help(object):
    def __init__(self, subject, owner):
        self.subject = subject
        self.owner = owner
        self.prepared = False

    def prepare(self):
        """Override for stuff to be done once per subject"""
        self.prepared = True

    def prepare_once(self):
        if not self.prepared:
            self.prepare()

    @runner.Clize(hide_help=True)
    @kwoargs('usage')
    @annotate(name=parameters.pass_name, args=parser.Parameter.UNDOCUMENTED)
    def cli(self, name, usage=False, *args):
        """Show the help

        usage: Only show the full usage
        """
        self.prepare_once()
        name = name.rpartition(' ')[0]
        f = util.Formatter()
        if usage:
            f.extend(self.show_full_usage(name))
        else:
            f.extend(self.show(name))
        return six.text_type(f)

def split_docstring(s):
    if not s:
        return
    code_coming = False
    code = False
    for p in p_delim.split(s):
        if (code_coming or code) and p.startswith(' '):
            yield p
            code_coming = False
            code = True
        else:
            item = ' '.join(p.split())
            if item.endswith(':'):
                code_coming = True
                if item == ':':
                    continue
            code = False
            yield item


def pname(p):
    return getattr(p, 'argument_name', p.display_name)


def filter_undocumented(params):
    for param in params:
        if not param.undocumented:
            yield param


LABEL_POS = "Arguments:"
LABEL_OPT = "Options:"
LABEL_ALT = "Other actions:"

class ClizeHelp(Help):
    @property
    def signature(self):
        return self.subject.signature

    @classmethod
    def get_param_type(cls, param):
        try:
            param.aliases
        except AttributeError:
            return LABEL_POS
        else:
            return LABEL_OPT


    def prepare(self):
        super(ClizeHelp, self).prepare()
        s = self.sections = util.OrderedDict((
            (LABEL_POS, util.OrderedDict()),
            (LABEL_OPT, util.OrderedDict()),
            (LABEL_ALT, util.OrderedDict()),
            ))
        self.after = {}
        for p in filter_undocumented(self.signature.positional):
            s[LABEL_POS][pname(p)] = p, ''
        for p in sorted(
                filter_undocumented(self.signature.named), key=pname):
            s[LABEL_OPT][pname(p)] = p, ''
        for p in sorted(
                filter_undocumented(self.signature.alternate), key=pname):
            s[LABEL_ALT][pname(p)] = p, ''
        self._parse_help()
        s[LABEL_ALT] = s.pop(LABEL_ALT)

    argdoc_re = re.compile(r'^(\w+): ?(.+)$')
    def parse_docstring(self, s, pnames=None):
        free_text = []
        header = []
        label = None
        last_argname = None
        for p in split_docstring(s):
            argdoc = self.argdoc_re.match(p)
            if argdoc:
                argname, text = argdoc.groups()
                if free_text:
                    if free_text[-1].endswith(':'):
                        label = free_text.pop()
                    if last_argname:
                        if pnames is None or last_argname in pnames:
                            self.after[last_argname] = free_text
                    else:
                        header.extend(free_text)
                    free_text = []
                last_argname = argname
                try:
                    default_label = self.get_param_type(
                        self.signature.parameters[argname])
                except KeyError:
                    continue
                if pnames is not None and argname not in pnames:
                    continue
                if default_label != LABEL_POS:
                    try:
                        param, _ = self.sections[default_label].pop(argname)
                    except KeyError:
                        continue
                    label_ = label or default_label
                    if label_ not in self.sections:
                        self.sections[label_] = util.OrderedDict()
                else:
                    try:
                        param, _ = self.sections[default_label][argname]
                    except KeyError:
                        continue
                    label_ = default_label
                self.sections[label_][argname] = param, text
            else:
                free_text.append(p)
        if not last_argname:
            header = free_text
            footer = []
        else:
            footer = free_text
        return lines_to_paragraphs(header), lines_to_paragraphs(footer)

    def parse_func_help(self, obj, pnames=None):
        """gets the information from obj's docstring and adds it to this
        help instance.

        If set, only parameters in pnames are added
        """
        return self.parse_docstring(inspect.getdoc(obj), pnames)

    def _parse_subject_help(self, subject):
        ret = self.parse_func_help(subject.func)
        for p in subject.signature.parameters.values():
            p.prepare_help(self)
        return ret

    def _params_prepare(self):
        for p in self.subject.signature.parameters.values():
            p.prepare_help(self)

    def _parse_help_wrappers(self, wrapper_funcs):
        self.header, self.footer = self.parse_func_help(self.subject)
        self._params_prepare()
        for wrapper in wrapper_funcs:
            self.parse_func_help(wrapper)

    def _parse_help_autosig(self, sig):
        self.header = []
        self.footer = []
        self._params_prepare()
        funcs = util.OrderedDict()
        for pname in sig.parameters:
            for func in sig.sources[pname]:
                funcs.setdefault(func, set()).add(pname)
        funcs = sorted(
            funcs.items(),
            key=lambda i: sig.sources['+depths'].get(i[0], 1000))
        funcs.insert(0, funcs.pop())
        for func, pnames in funcs:
            h, f = self.parse_func_help(func, pnames)
            self.header.extend(h)
            self.footer.extend(f)

    def _parse_help(self):
        wrapper_funcs = list(wrappers(self.subject.func))
        sig = self.subject.func_signature
        if wrapper_funcs or not sig.parameters:
            self._parse_help_wrappers(wrapper_funcs)
        else:
            self._parse_help_autosig(sig)

    @property
    def description(self):
        self.prepare_once()
        try:
            return self.header[0]
        except IndexError:
            return ''

    def show_usage(self, name):
        return 'Usage: {name}{options}{space}{positional}'.format(
            name=name,
            options=' [OPTIONS]' if self.signature.named else '',
            space=' ' if self.signature.positional else '',
            positional=' '.join(
                str(arg)
                for arg in filter_undocumented(self.signature.positional))
            ),

    def alternate_usages(self):
        for param in self.signature.alternate:
            if param.undocumented:
                continue
            subname = param.display_name
            try:
                helper = param.func.helper
            except AttributeError:
                yield subname + ' [args...]'
            else:
                for usage in helper.usages():
                    yield subname + ' ' + usage

    def usages(self):
        yield str(self.signature)
        for usage in self.alternate_usages():
            yield usage

    def show_full_usage(self, name):
        for usage in self.usages():
            yield name + ' ' + usage

    def show_arguments(self):
        f = util.Formatter()
        with f.columns(indent=2) as cols:
            for label, section in self.sections.items():
                if not section: continue
                f.new_paragraph()
                f.append(label)
                for argname, (param, text) in section.items():
                    self.show_argument(
                        param,
                        text, self.after.get(argname, ()),
                        f, cols)
        return f

    def show_argument(self, param, desc, after, f, cols):
        ret = param.show_help(desc, after, f, cols)
        if ret is not None:
            cols.append(*ret)
            if after:
                f.new_paragraph()
                f.extend(after)
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
                    try:
                        desc = command.helper.description
                    except AttributeError:
                        desc = ''
                    cols.append(', '.join(names), desc)
        return f

    def prepare_notes(self, doc):
        if doc is None:
            return ()
        else:
            return lines_to_paragraphs(split_docstring(inspect.cleandoc(doc)))

    def prepare(self):
        super(DispatcherHelper, self).prepare()
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

    def usages(self):
        yield self.subject.help_aliases[0] + ' ' + str(self.cli.signature)
        for names, subcommand in self.owner.cmds.items():
            try:
                get_usages = subcommand.helper.usages
            except AttributeError:
                yield names[0] + ' [args...]'
            else:
                for usage in get_usages():
                    yield names[0] + ' ' + usage

    def show_full_usage(self, name):
        for usage in self.usages():
            yield name + ' ' + usage
