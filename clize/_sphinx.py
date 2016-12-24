# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

"""Adds auto- and domain directives that don't clash the referencing system"""
from sphinx.domains import python
from sphinx.ext import autodoc


class NoDupesObjectDirective(python.PyObject):
    def get_ref_context(self):
        try:
            return self.env.ref_context
        except AttributeError:
            return self.env.temp_data

    def add_target_and_index(self, name_cls, sig, signode):
        modname = self.options.get(
            'module', self.get_ref_context().get('py:module'))
        fullname = (modname and modname + '.' or '') + name_cls[0]
        # note target
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)

        indextext = self.get_index_text(modname, name_cls)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname, '', None))

    def get_index_text(self, *args, **kwargs):
        back = self.objtype
        try:
            self.objtype = back[4:]
            return super(NoDupesObjectDirective, self
                ).get_index_text(*args, **kwargs)
        finally:
            self.objtype = back


class MoreInfoDocumenter(autodoc.Documenter):
    def __init__(self, *args, **kwargs):
        super(MoreInfoDocumenter, self).__init__(*args, **kwargs)
        self.__fixed = False

    def add_directive_header(self, sig):
        if not self.__fixed:
            directive = getattr(self, 'directivetype', self.objtype)
            self.directivetype = 'more' + directive
        return super(MoreInfoDocumenter, self).add_directive_header(sig)

    def can_document_member(self, *args):
        return False


class MoreInfoDirective(autodoc.AutoDirective):
    _registry = {}

    def run(self, *args, **kwargs):
        return super(MoreInfoDirective, self).run(*args, **kwargs)


def add_moredoc(app, objtype):
    cls = autodoc.AutoDirective._registry[objtype]
    documenter = type('More'+cls.__name__, (MoreInfoDocumenter, cls), {})
    autodoc.AutoDirective._registry['more' + objtype] = documenter
    app.add_directive('automore' + objtype, autodoc.AutoDirective)

    dirname = getattr(cls, 'directivetype', cls.objtype)
    dircls = python.PythonDomain.directives[dirname]
    directive = type("NoDupes"+dircls.__name__,
                     (NoDupesObjectDirective, dircls), {})
    python.PythonDomain.directives['more' + dirname] = directive
    #app.add_directive('py:more' + dirname, directive)


def setup(app):
    for name in list(autodoc.AutoDirective._registry):
        add_moredoc(app, name)
