from clize import run, parser, errors


class _ShowList(Exception):
    pass


class OneOfParameter(parser.ParameterWithValue):
    def __init__(self, values, **kwargs):
        super().__init__(**kwargs)
        self.values = values

    def coerce_value(self, arg, ba):
        if arg == 'list':
            raise _ShowList
        elif arg in self.values:
            return arg
        else:
            raise errors.BadArgumentFormat(arg)

    def read_argument(self, ba, i):
        try:
            super(OneOfParameter, self).read_argument(ba, i)
        except _ShowList:
            ba.func = self.show_list
            ba.args[:] = []
            ba.kwargs.clear()
            ba.sticky = parser.IgnoreAllArguments()
            ba.posarg_only = True

    def show_list(self):
        for val in self.values:
            print(val)

    def help_parens(self):
        for s in super(OneOfParameter, self).help_parens():
            yield s
        yield 'use "list" for options'


def one_of(*values):
    return parser.use_mixin(OneOfParameter, kwargs={'values': values})


def func(breakfast:one_of('ham', 'spam')):
    """Serves breakfast

    :param breakfast: what food to serve
    """
    print("{0} is served!".format(breakfast))


run(func)
