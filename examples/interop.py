import argparse

from clize import Clize, parameters, run


@Clize.as_is(description="Prints argv separated by pipes")
def echo_argv(*args):
    print(*args, sep=' | ')


def using_argparse(name: parameters.pass_name, *args):
    parser = argparse.ArgumentParser(prog=name)
    parser.add_argument('--ham')
    ns = parser.parse_args(args=args)
    print(ns.ham)


run(echo_argv,
    Clize.as_is(using_argparse,
                description="Prints the value of the --ham option",
                usages=['--help', '[--ham HAM]']))
