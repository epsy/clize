# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

"""
`clize.help` manages the generation of help messages obtained using ``--help``.

`.HelpCli` is the command-line interface for it. It is injected as an extra
alternate option by `.Clize`. It can be replaced using `.Clize`'s
``helper_class`` parameter.

`.HelpForClizeDocstring` constructs the help for clize's docstring format.
It is invoked by `.HelpCli.get_help` method. It can be swapped with the
``builder`` parameter of `.HelpCli`.

It uses `sigtools.specifiers.signature` to obtain which functions document the
parameters, `.elements_from_clize_docstring` and `.helpstream_from_elements`
process the docstring so it can be fed to
`.HelpForClizeDocstring.add_docstring`.

"""

import sys
import io
import itertools
import inspect
import re

import od
import attr
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from docutils import nodes as dunodes, transforms, frontend
from docutils.transforms import references
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
"""The label for positional parameters"""


LABEL_OPT = "Options"
"""The default label for named parameters"""


LABEL_ALT = "Other actions"
"""The label for alternate actions like ``--help``"""


@attr.s
class HelpForParameters(object):
    """Stores and displays help for a CLI with positional parameters,
    named parameters and/or alternate actions designated by a named parameter

    Example output in relation to attribute names::

        header

        section:
            param1   Param1 description

        After param2

            param2   Param2 description

        footer

    .. attribute:: header
        :annotation: = []

        A list of strings representing paragraphs in the help
        header/description.

    .. attribute:: footer
        :annotation: = []

        A list of strings representing paragraphs in the help
        footer after everything else.

    .. attribute:: sections
        :annotation: = OrderedDict("section_name" =>
            OrderedDict("param_name" =>
                (param, "description")))

        Maps section names to parameters and their help.

    .. attribute:: after
        :annotation: = {"param_name": ["paragraph"]}

        Maps parameter names to additional paragraphs.
    """

    header = attr.ib()
    footer = attr.ib()
    sections = attr.ib()
    after = attr.ib()

    @classmethod
    def blank_from_signature(cls, signature):
        """Creates a blank instance with placeholders for the parameters in
        ``signature``.

        The parameters are sorted into three sections:

        ============ ===================================
        `.LABEL_POS` Positional parameters
        `.LABEL_OPT` Named parameters
        `.LABEL_ALT` Alternate options (e.g. ``--help``)
        ============ ===================================
        """
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
        """Returns a summary overview of the command's parameters.

        Option parameters are collapsed as ``[OPTIONS]`` in the output.
        """
        ret = ['Usage:', name]
        if self._has_options:
            ret.append('[OPTIONS]')
        ret.extend(
            str(param)
            for param, _ in self.sections[LABEL_POS].values())
        return ' '.join(ret),

    def _alternate_usages(self):
        return _alternate_usages(self._alternate_params)

    def usages(self):
        """Returns an iterable of all possible complete usage patterns"""
        yield ' '.join(str(param) for param in self._params_for_usage)
        for usage in self._alternate_usages():
            yield usage

    def show_full_usage(self, name):
        """Returns an iterable of all possible complete usage patterns
        including the command name"""
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
        """Produce the full help."""
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
    """Converts a string to an iterable of element tuples such as
    ``(EL_FREE_TEXT, "text", False)``.

    The result is suitable for `helpstream_from_elements`.

    See below for which tuples are produced/understood.
    """
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


EL_LABEL = util.Sentinel('EL_LABEL')
"""``(EL_LABEL, "label")``

Indicates that the subsequent `EL_PARAM_DESC` elements are under a section
label.
"""


EL_FREE_TEXT = util.Sentinel('EL_FREE_TEXT')
"""``(EL_FREE_TEXT, "paragraph", is_preformatted)``

Designates some free text. May be converted into header text, footer text, or
additional paragraphs after a parameter depending on context.

The last free text elements at the end of a docstring are always considered
to be the footer rather than additional paragraphs after a parameter.

``is_preformatted`` is a boolean that indicates that the paragraph should not
be reformatted.
"""


EL_PARAM_DESC = util.Sentinel('EL_PARAM_DESC')
"""``(EL_PARAM_DESC, "param", "paragraph")``

Designates the description for a parameter.
"""


EL_AFTER = util.Sentinel('EL_AFTER')
"""``(EL_AFTER, "param", "paragraph", is_preformatted)``

Explicitly designates an additional paragraph after a parameter. Unlike
`EL_FREE_TEXT`, this cannot be confused for a footer paragraph.
"""


def helpstream_from_elements(tokens):
    """
    Transforms an iterable of non-explicit ``EL_*`` elements to an iterable of
    explicit ``HELP_*`` elements.

    The result is suitable for `HelpForClizeDocstring.add_helpstream`.
    """
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
            elif ttype == EL_AFTER:
                name, text, preformatted = args
                yield (HELP_PARAM_AFTER,) + args
            else:
                raise ValueError("Unknown token: " + str(ttype))
    if prev_param is None:
        for ftext in free_text:
            yield (HELP_HEADER,) + ftext
    else:
        for ftext in free_text:
            yield (HELP_FOOTER,) + ftext


HELP_HEADER = util.Sentinel('HELP_HEADER')
"""``(HELP_HEADER, "paragraph", is_preformatted)``

Designates a paragraph that appears before the parameter descriptions.
"""
HELP_FOOTER = util.Sentinel('HELP_FOOTER')
"""``(HELP_FOOTER, "paragraph", is_preformatted)``

Designates a paragraph that appears after the parameter descriptions.
"""
HELP_PARAM_DESC = util.Sentinel('HELP_PARAM_DESC')
"""``(HELP_PARAM_DESC, "param", "label", "paragraph")``

Designates a parameter description. If no label was specified `None` should take its
place.
"""
HELP_PARAM_AFTER = util.Sentinel('HELP_PARAM_AFTER')
"""``(HELP_PARAM_AFTER, "param", "paragraph", is_preformatted)``

Designates a paragraph after a parameter description.
"""


def elements_from_autodetected_docstring(docstring, name, _docutils_frontend_module=frontend):
    if not docstring:
        return ()
    document, errout = _document_from_sphinx_docstring(docstring, name, _docutils_frontend_module)
    if document.next_node(dunodes.field_list, include_self=True) is None:
        return elements_from_clize_docstring(docstring)
    else:
        sys.stderr.write(errout)
        return elements_from_sphinx_document(document)


class HelpForAutodetectedDocstring(HelpForParameters):
    """Builds generic parameter help from the docstrings of Clize instances

    Uses a custom docstring format. See :ref:`clize docstring`.
    """

    def __init__(self, *args, **kwargs):
        super(HelpForAutodetectedDocstring, self).__init__(*args, **kwargs)
        self._documented = set()

    @classmethod
    def from_subject(cls, subject, owner):
        """Constructs a `HelpForClizeDocstring` instance and populates it with
        data from a `.Clize` instance.

        It uses the parameters' `.parser.Parameter.prepare_help` and reads
        the docstrings of functions from which the parameters originate.

        :param .Clize subject: The `.Clize` instance to document.
        :param object owner: The object of which ``subject`` is a member of,
            or `None`.

            This typically has a value if a CLI is defined as a class::

                class MyCli(object):
                    @clize.Clize
                    def cli(self, param):
                        ...

            ``owner`` would refer to an instance of ``MyCli``.
        """
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
        """Uses `.parser.Parameter.prepare_help` on an iterable of parameters"""
        for param in parameters:
            param.prepare_help(self)

    def add_from_parameter_sources(self, subject):
        """Processes the docstrings of the functions that have parameters
        in ``subject`` and adds their information to this instance.

        :param .Clize subject: the Clize runner to document
        """
        func_signature = subject.func_signature
        funcs = util.OrderedDict()
        for pname in func_signature.parameters:
            for func in func_signature.sources[pname]:
                funcs.setdefault(func, set()).add(pname)
        for func in func_signature.sources['+depths']:
            funcs.setdefault(func, set())
        funcs = sorted(
            funcs.items(),
            key=lambda i: func_signature.sources['+depths'].get(i[0], 1000))
        real_subject = self._pop_real_subject(funcs, subject) or subject
        self.add_docstring(inspect.getdoc(real_subject), real_subject.__name__, None, True)
        for func, pnames in funcs:
            try:
                fname = func.__name__
            except AttributeError:
                pass
            else:
                self.add_docstring(
                    inspect.getdoc(func), fname,
                    pnames - self._documented, False)

    def add_docstring(self, docstring, name, pnames, primary):
        """Parses and integrates info from a docstring to this instance.

        :param str docstring: The docstring to be read. Must be de-indented
            using something like `inspect.cleandoc`.
        :param set pnames: If not `None`, only add info about these parameter
            names.
        :param bool primary: Add headers and footers from this docstring.
        """
        self.add_helpstream(
            helpstream_from_elements(
                elements_from_autodetected_docstring(docstring, name)),
            pnames, primary)

    def parse_docstring(self, docstring):
        """Alias of `add_docstring` for backwards compatibility."""
        self.add_docstring(docstring, "docstring", None, False)

    def add_helpstream(self, stream, pnames, primary):
        """Add an iterable of tuples starting with ``HELP_`` to this instance.

        :param iterable stream: An iterable of ``(HELP_*, ...)`` tuples,
            as produced by `helpstream_from_elements`
        :param set pnames: If not `None`, only add info about these parameter
            names.
        :param bool primary: Add headers and footers from this docstring.
        """
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


class HelpForClizeDocstring(HelpForAutodetectedDocstring):
    def add_docstring(self, docstring, name, pnames, primary):
        """Parses a Clize docstring."""
        self.add_helpstream(
            helpstream_from_elements(
                elements_from_clize_docstring(docstring)),
            pnames, primary)


class _NodeSeeker(dunodes.GenericNodeVisitor, object):
    def __init__(self, node, *args, **kwargs):
        include = kwargs.pop('include')
        exclude = kwargs.pop('exclude', (dunodes.system_message,))
        super(_NodeSeeker, self).__init__(*args, **kwargs)
        self.node = node
        self.include = include
        self.exclude = exclude
        self.result = []

    def __iter__(self):
        return iter(self.result)

    def default_visit(self, node):
        if isinstance(node, self.exclude) and node != self.node:
            raise dunodes.SkipChildren
        elif isinstance(node, self.include):
            self.result.append(node)


def _findall_iter(node):
    """Backwards compatibility pre Docutils 0.19"""
    try:
        findall = node.findall
    except AttributeError:
        return node.traverse()
    else:
        return findall()


def _du_field_name_and_body(node):
    name = None
    body = None
    for n in _findall_iter(node):
        if isinstance(n, dunodes.field_name):
            name = n
        elif isinstance(n, dunodes.field_body):
            body = n
    return name, body


_NEWLINE_PAT = re.compile(r'(?P<dot>\.?)\n+')


def _replace_newline(match):
    if match.group('dot'):
        return '.  '
    else:
        return ' '


def _remove_newlines(text):
    return _NEWLINE_PAT.sub(_replace_newline, text)


def _is_label(text, node):
    next_node = node.next_node(descend=False, ascend=True)
    return (
        text.endswith(':')
        and isinstance(next_node, dunodes.field_list)
        )


class _SphinxVisitor(dunodes.SparseNodeVisitor, object):
    def __init__(self, *args, **kwargs):
        super(_SphinxVisitor, self).__init__(*args, **kwargs)
        self.result = []

    def seek_nodes(self, node, include, exclude=(dunodes.system_message)):
        visitor = _NodeSeeker(node, self.document, include=include, exclude=exclude)
        node.walk(visitor)
        return list(visitor)

    def text(self, *args, **kwargs):
        return ''.join(
            node.astext()
            for node in self.seek_nodes(*args, include=(dunodes.Text,), **kwargs)
        )

    def visit_paragraph(self, node):
        text = self.text(node)
        if _is_label(text, node):
            self.result.append(
                (EL_LABEL, text[:-1])
            )
        else:
            self.result.append(
                (EL_FREE_TEXT, _remove_newlines(self.text(node)), False)
            )
        raise dunodes.SkipChildren

    def indent_preformatted(self, text):
        return '\n'.join('    ' + line for line in text.split('\n'))

    def visit_literal_block(self, node):
        self.result.append(
            (EL_FREE_TEXT, self.indent_preformatted(self.text(node)), True)
        )
        raise dunodes.SkipChildren

    def visit_field(self, node):
        name, body = _du_field_name_and_body(node)
        options = self.text(name).split()
        if options[0] == 'param':
            param = options[-1]
            paragraphs = self.seek_nodes(body, include=(dunodes.paragraph, dunodes.literal_block))
            description = ""
            if paragraphs and isinstance(paragraphs[0], dunodes.paragraph):
                description = _remove_newlines(self.text(paragraphs.pop(0)))
            self.result.append(
                (EL_PARAM_DESC, param, description)
            )
            for p in paragraphs:
                text = self.text(p)
                preformatted = True
                if isinstance(p, dunodes.paragraph):
                    preformatted = False
                    text = _remove_newlines(text)
                else:
                    text = self.indent_preformatted(text)
                self.result.append(
                    (EL_AFTER, param, text, preformatted)
                )
        raise dunodes.SkipChildren

    def visit_system_message(self, node):
        raise dunodes.SkipChildren

    def __iter__(self):
        return iter(self.result)


def _get_default_docutils_settings(_docutils_frontend_module):
    try:
        get = _docutils_frontend_module.get_default_settings
    except AttributeError:
        return _docutils_frontend_module.OptionParser(components=(Parser,)).get_default_values()
    else:
        return get(Parser)


def _document_from_sphinx_docstring(source, name, _docutils_frontend_module):
    """Reads a Sphinx.autodoc-compatible docstring into something
    `helpstream_from_elements` can process.
    """
    parser = Parser()
    settings = _get_default_docutils_settings(_docutils_frontend_module)
    errout = settings.warning_stream = io.StringIO()
    document = new_document(name, settings)
    parser.parse(source, document)
    transformer = transforms.Transformer(document)
    transformer.add_transform(references.Substitutions)
    transformer.apply_transforms()
    return document, errout.getvalue()

def elements_from_sphinx_document(document):
    visitor = _SphinxVisitor(document)
    document.walk(visitor)
    return visitor

def elements_from_sphinx_docstring(docstring, name):
    document, errout = _document_from_sphinx_docstring(docstring, name, frontend)
    sys.stderr.write(errout)
    return elements_from_sphinx_document(document)


class HelpForSphinxDocstring(HelpForClizeDocstring):
    """Builds generic parameter help from the docstrings of Clize instances

    Understands docstrings written for Sphinx's :rst:dir:`autodoc
    <sphinx:autofunction>`."""

    def add_docstring(self, docstring, name, pnames, primary):
        self.add_helpstream(
            helpstream_from_elements(
                elements_from_sphinx_docstring(docstring, name),
            ), pnames, primary)


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
    """Stores help for subcommand dispatchers.

    .. attribute:: subcommands

        An ordered mapping of the subcommand names to their description.

    .. attribute:: header

        Iterable of paragraphs for the help header.

    .. attribute:: footer

        Iterable of paragraphs for the help footnotes.
    """
    _usages = attr.ib()
    subcommands = attr.ib()
    header = attr.ib()
    footer = attr.ib()

    @classmethod
    def from_subject(cls, subject, owner):
        """Constructs a `.HelpForSubcommands` instance and populates it with
        data from a `.Clize` instance.

        It uses the parameters' `.parser.Parameter.prepare_help` and reads
        the docstrings of functions from which the parameters originate.

        :param .Clize subject: The `.Clize` instance to document.
        :param .SubcommandDispatcher owner: The subcommand dispatcher being
            documented.
        """
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
        """Produce the full help."""
        f = util.Formatter()
        f.extend(self.show_usage(name))
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.header))
        f.new_paragraph()
        f.extend(self._show_subcommands())
        f.new_paragraph()
        f.extend(_lines_to_paragraphs(self.footer))
        return f

    def _show_subcommands(self):
        f = util.Formatter()
        f.append('Commands:')
        with f.indent():
            with f.columns() as cols:
                for names, description in self.subcommands.items():
                    cols.append(', '.join(names), description)
        return f

    def show_usage(self, name):
        """Returns a summary overview of the dispatcher's command format."""
        yield 'Usage: {0} command [args...]'.format(name)

    def show_full_usage(self, name):
        """Returns an iterable of all possible complete usage patterns
        for subcommands including the command name"""
        for usage in self.usages():
            yield name + ' ' + usage

    def usages(self):
        """Returns an iterable of all possible complete usage patterns for
        all subcommands"""
        for usage in self._usages:
            yield usage


class HelpCli(object):
    """A command-line interface for constructing and accessing the help
    and other meta-information about a CLI"""

    def __init__(self, subject, owner,
                 builder=HelpForAutodetectedDocstring.from_subject):
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
        return str(f)

    def get_help(self):
        """Get the object """
        return self.builder(self.subject, self.owner)

    @property
    def description(self):
        """A short description of this command"""
        header = self.get_help().header
        if header:
            return header[0]
        else:
            return ""

    def prepare(self):
        pass # No-op for backwards-compatibility

    def show(self, name):
        """Legacy alias of ``get_help().show_help(...)``"""
        return self.get_help().show_help(name)

    def show_full_usage(self, name):
        """Legacy alias of ``get_help().show_full_usage(...)``"""
        return self.get_help().show_full_usage(name)

    def show_usage(self, name):
        """Legacy alias of ``get_help().show_usage(...)``"""
        return self.get_help().show_usage(name)

    def usages(self):
        """Legacy alias of ``get_help().usages(...)``"""
        return self.get_help().usages()


ClizeHelp = HelpCli
