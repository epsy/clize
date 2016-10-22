# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

from __future__ import unicode_literals

import itertools
import inspect
import re

import od
import attr
import six
from sigtools.modifiers import annotate, kwoargs

from clize import runner, parser, util, parameters


def _lines_to_paragraphs(L):
    return list(itertools.chain.from_iterable((x, '') for x in L))


def _pname(p):
    return getattr(p, 'argument_name', p.display_name)


def _filter_undocumented(params):
    for param in params:
        if not param.undocumented:
            yield param


LABEL_POS = "Arguments"
LABEL_OPT = "Options"
LABEL_ALT = "Other actions"

EL_LABEL = util.Sentinel('EL_LABEL')
EL_FREE_TEXT = util.Sentinel('EL_FREE_TEXT')
EL_PARAM_DESC = util.Sentinel('EL_PARAM_DESC')

HELP_HEADER = util.Sentinel('HELP_HEADER')
HELP_FOOTER = util.Sentinel('HELP_FOOTER')
HELP_PARAM_DESC = util.Sentinel('HELP_PARAM_DESC')
HELP_PARAM_AFTER = util.Sentinel('HELP_PARAM_AFTER')


@attr.s
class HelpForParameters(object):
    """Stores and displays help for a CLI with positional parameters,
    named parameters and/or alternate actions designated by a named parameter
    """
    header = attr.ib()
    footer = attr.ib()
    sections = attr.ib()
    after = attr.ib()

    @classmethod
    def blank_from_signature(cls, signature):
        s = util.OrderedDict((
            (LABEL_POS, util.OrderedDict()),
            (LABEL_OPT, util.OrderedDict()),
            (LABEL_ALT, util.OrderedDict()),
            ))
        for p in _filter_undocumented(signature.positional):
            s[LABEL_POS][_pname(p)] = p, ''
        for p in sorted(
                _filter_undocumented(signature.named), key=_pname):
            s[LABEL_OPT][_pname(p)] = p, ''
        for p in _filter_undocumented(signature.alternate):
            s[LABEL_ALT][_pname(p)] = p, ''
        return cls([], [], s, {})

    @property
    def _has_options(self):
        if self.sections[LABEL_OPT]:
            return True
        return any(title not in (LABEL_POS, LABEL_OPT, LABEL_ALT)
                   for title in self.sections)

    @property
    def _all_params(self):
        return (
            param
            for title, section in self.sections.items()
            for param, _ in section.values()
        )

    @property
    def _params_for_usage(self):
        for title, section in self.sections.items():
            if title not in (LABEL_POS, LABEL_ALT):
                for param, _ in section.values():
                    yield param
        for param, _ in self.sections[LABEL_POS].values():
            yield param

    @property
    def _alternate_params(self):
        return (
            param
            for param, _ in self.sections[LABEL_ALT].values()
        )

    def show_usage(self, name):
        return 'Usage: {name}{options}{space}{positional}'.format(
            name=name,
            options=' [OPTIONS]' if self._has_options else '',
            space=' ' if self.sections[LABEL_POS] else '',
            positional=' '.join(
                str(param)
                for param, _ in self.sections[LABEL_POS].values())
            ),

    def _alternate_usages(self):
        return _alternate_usages(self._alternate_params)

    def usages(self):
        yield ' '.join(str(param) for param in self._params_for_usage)
        for usage in self._alternate_usages():
            yield usage

    def show_full_usage(self, name):
        for usage in self.usages():
            yield name + ' ' + usage

    def _show_parameters(self):
        f = util.Formatter()
        with f.columns(indent=2) as cols:
            for label, section in self.sections.items():
                if not section: continue
                f.new_paragraph()
                f.append(label + ':')
                for argname, (param, text) in section.items():
                    self._show_parameter(
                        param,
                        text, self.after.get(argname, ()),
                        f, cols)
        return f

    def _show_parameter(self, param, desc, after, f, cols):
        ret = param.show_help(desc, after, f, cols)
        if ret is not None:
            cols.append(*ret)
            if after:
                f.new_paragraph()
                f.extend(after)
                f.new_paragraph()

    def show_help(self, name):
        f = util.Formatter()
        f.extend(self.show_usage(name))
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.header))
        f.new_paragraph()
        f.extend(self._show_parameters())
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.footer))
        return f


_p_delim = re.compile(r'\n\s*\n')


def _split_clize_docstring(s):
    if not s:
        return
    code_coming = False
    code = False
    for p in _p_delim.split(s):
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


CLIZEDOC_ARGUMENT_RE = re.compile(r'^(\w+): ?(.+)$')


def elements_from_clize_docstring(source):
    free_text = None
    for p in _split_clize_docstring(source):
        if p.startswith(' '):
            if free_text is not None:
                yield EL_FREE_TEXT, free_text, False
                free_text = None
            yield EL_FREE_TEXT, p, True
            continue
        argdoc = CLIZEDOC_ARGUMENT_RE.match(p)
        if argdoc:
            argname, text = argdoc.groups()
            if free_text is not None:
                if free_text.endswith(':'):
                    yield EL_LABEL, free_text[:-1]
                    free_text = None
                if free_text is not None:
                    yield EL_FREE_TEXT, free_text, False
                    free_text = None
            yield EL_PARAM_DESC, argname, text
        else:
            if free_text is not None:
                yield EL_FREE_TEXT, free_text, False
                free_text = None
            free_text = p
    if free_text is not None:
        yield EL_FREE_TEXT, free_text, False


def helpstream_from_elements(tokens):
    label = None
    prev_param = None
    free_text = []
    for token in tokens:
        ttype, args = token[0], token[1:]
        if ttype == EL_FREE_TEXT:
            text, preformatted = args
            free_text.append((text, preformatted))
        else:
            if prev_param is None:
                for ftext in free_text:
                    yield (HELP_HEADER,) + ftext
            else:
                for ftext in free_text:
                    yield (HELP_PARAM_AFTER, prev_param) + ftext
            free_text = []
            if ttype == EL_LABEL:
                label, = args
            elif ttype == EL_PARAM_DESC:
                name, description = args
                prev_param = name
                yield HELP_PARAM_DESC, name, label, description
            else:
                raise ValueError("Unknown token: " + str(ttype))
    if prev_param is None:
        for ftext in free_text:
            yield (HELP_HEADER,) + ftext
    else:
        for ftext in free_text:
            yield (HELP_FOOTER,) + ftext


class HelpForClizeDocstring(HelpForParameters):
    """Builds generic parameter help from the docstrings of Clize instances

    Uses a custom docstring format. See :ref:`clize docstring`.
    """

    def __init__(self, *args, **kwargs):
        super(HelpForClizeDocstring, self).__init__(*args, **kwargs)
        self._documented = set()

    @classmethod
    def from_subject(cls, subject, owner):
        ret = cls.blank_from_signature(subject.signature)
        ret.add_from_parameters(subject.signature.parameters.values())
        ret.add_from_parameter_sources(subject)
        return ret

    @classmethod
    def _get_param_type(cls, param):
        try:
            param.aliases
        except AttributeError:
            return LABEL_POS
        else:
            return LABEL_OPT

    @property
    def _parameters(self):
        return {
            param.argument_name: param
            for param in self._all_params
            if hasattr(param, 'argument_name')
        }

    def _pop_real_subject(self, funcs, subject):
        for i, (func, pnames) in enumerate(reversed(funcs), 1):
            if func.__name__ == subject.__name__:
                break
        else:
            return None
        return funcs.pop(len(funcs) - i)[0]

    def add_from_parameters(self, parameters):
        for param in parameters:
            param.prepare_help(self)

    def add_from_parameter_sources(self, subject):
        func_signature = subject.func_signature
        funcs = util.OrderedDict()
        for pname in func_signature.parameters:
            for func in func_signature.sources[pname]:
                funcs.setdefault(func, set()).add(pname)
        funcs = sorted(
            funcs.items(),
            key=lambda i: func_signature.sources['+depths'].get(i[0], 1000))
        real_subject = self._pop_real_subject(funcs, subject) or subject
        self.add_docstring(inspect.getdoc(real_subject), None, True)
        for func, pnames in funcs:
            self.add_docstring(
                inspect.getdoc(func), pnames - self._documented, False)

    def parse_docstring(self, docstring):
        self.add_docstring(docstring, None, False)

    def add_docstring(self, docstring, pnames, primary):
        self.add_helpstream(
            helpstream_from_elements(
                elements_from_clize_docstring(docstring)),
            pnames, primary)

    def add_helpstream(self, stream, pnames, primary):
        parameters = self._parameters
        for item in stream:
            ttype, args = item[0], item[1:]
            if ttype == HELP_HEADER:
                if primary:
                    self.header.append(args[0])
            elif ttype == HELP_FOOTER:
                if primary:
                    self.footer.append(args[0])
            elif ttype == HELP_PARAM_DESC:
                name, label, description = args
                if pnames is not None and name not in pnames:
                    continue
                try:
                    param = parameters[name]
                except KeyError:
                    continue
                default_label = self._get_param_type(parameters[name])
                if default_label == LABEL_POS:
                    final_label = default_label
                else:
                    self.sections[default_label].pop(name)
                    final_label = label or default_label
                if final_label not in self.sections:
                    self.sections[final_label] = util.OrderedDict()
                self.sections[final_label][name] = param, description
                self._documented.add(name)
            elif ttype == HELP_PARAM_AFTER:
                name, description, preformatted = args
                if pnames is not None and name not in pnames:
                    continue
                self.after.setdefault(name, []).append(description)
            else:
                raise ValueError("Unknown help item type: " + repr(ttype))
        self.sections[LABEL_ALT] = self.sections.pop(LABEL_ALT)


def _alternate_usages(alternate_params):
    for param in alternate_params:
        subname = param.display_name
        try:
            helper = param.func.helper
        except AttributeError:
            yield subname + ' [args...]'
        else:
            for usage in helper.get_help().usages():
                yield subname + ' ' + usage


@attr.s
class HelpForSubcommands(object):
    _usages = attr.ib()
    subcommands = attr.ib()
    header = attr.ib()
    footer = attr.ib()

    @classmethod
    def from_subject(cls, subject, owner):
        usages = cls._get_usages(subject.signature.alternate, owner.cmds.items())
        subcommands = od(
            (names, cls._get_description(command))
            for names, command in owner.cmds.items()
        )
        header = footer = ()
        if owner.description:
            header = cls._get_free_text(
                elements_from_clize_docstring(inspect.cleandoc(owner.description)))
        if owner.footnotes:
            footer = cls._get_free_text(
                elements_from_clize_docstring(inspect.cleandoc(owner.footnotes)))
        return cls(list(usages), subcommands, list(header), list(footer))

    @classmethod
    def _get_description(cls, command):
        try:
            return command.helper.description
        except AttributeError:
            return ''

    @classmethod
    def _get_usages(cls, alternate_params, subcommands):
        for usage in _alternate_usages(alternate_params):
            yield usage
        for names, subcommand in subcommands:
            try:
                get_usages = subcommand.helper.usages
            except AttributeError:
                yield names[0] + ' [args...]'
            else:
                for usage in get_usages():
                    yield names[0] + ' ' + usage

    @classmethod
    def _get_free_text(cls, tokens):
        for token in tokens:
            ttype, args = token[0], token[1:]
            if ttype == EL_FREE_TEXT:
                yield args[0]

    def show_help(self, name):
        f = util.Formatter()
        f.extend(self.show_usage(name))
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.header))
        f.new_paragraph()
        f.extend(self.show_subcommands())
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.footer))
        return f

    def show_subcommands(self):
        f = util.Formatter()
        f.append('Commands:')
        with f.indent():
            with f.columns() as cols:
                for names, description in self.subcommands.items():
                    cols.append(', '.join(names), description)
        return f

    def show_usage(self, name):
        yield 'Usage: {0} command [args...]'.format(name)

    def show_full_usage(self, name):
        for usage in self.usages():
            yield name + ' ' + usage

    def usages(self):
        for usage in self._usages:
            yield usage


class HelpCli(object):
    """A command-line interface for constructing and accessing the help
    and other meta-information about a CLI"""

    def __init__(self, subject, owner,
                 builder=HelpForClizeDocstring.from_subject):
        self.subject = subject
        self.owner = owner
        self.builder = builder

    @runner.Clize(hide_help=True)
    @kwoargs('usage')
    @annotate(name=parameters.pass_name, args=parser.Parameter.UNDOCUMENTED)
    def cli(self, name, usage=False, *args):
        """Show the help

        usage: Only show the full usage
        """
        name = name.rpartition(' ')[0]
        f = util.Formatter()
        help = self.get_help()
        if usage:
            f.extend(help.show_full_usage(name))
        else:
            f.extend(help.show_help(name))
        return six.text_type(f)

    def get_help(self):
        return self.builder(self.subject, self.owner)

    def prepare(self):
        """No-op for compatibility"""

    def show(self, name):
        return self.get_help().show_help(name)

    def show_full_usage(self, name):
        return self.get_help().show_full_usage(name)

    def show_usage(self, name):
        return self.get_help().show_usage(name)

    def usages(self):
        return self.get_help().usages()

    @property
    def description(self):
        header = self.get_help().header
        if header:
            return header[0]
        else:
            return ""


ClizeHelp = HelpCli
