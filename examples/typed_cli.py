import pathlib
import typing

from clize import Clize, run, converters  # type: ignore


def main(
    # The ideal case: Clize and mypy understand the same annotation
    same_annotation_for_both_str: str,
    same_annotation_for_both_converter: pathlib.Path,
    *,
    # Unfortunately, Clize doesn't understand typing.Optional yet, and just uses int.
    # You'll have to separate the typing and Clize annotation using typing.Annotated
    optional_value: typing.Annotated[typing.Optional[int], Clize[int]] = None,
    # Perhaps confusingly, typing.Optional does not refer to whether a parameter is required,
    # only whether None is an acceptable value.
    optional_parameter: typing.Annotated[int, Clize[int]] = 1,
    # If you're using other clize annotations, like parameter aliases,
    # you'll have to use typing.Annotated
    aliased: typing.Annotated[int, Clize["n"]],
    # Value converters do not yet create typing annotations,
    # so you have to define the type separately using typing.Annotated.
    # Additionally, the type created by converters.file() is not public, so you have to rely on Any for now.
    file_opener: typing.Annotated[typing.Any, Clize[converters.file()]]
):
    """
    Example CLI that uses typing and Clize together

    In Clize 5.0 this remains fairly rudimentary,
    so you may have to repeat yourself
    when Clize and your type checker (e.g. mypy) do not understand the same annotation.
    """
    print(
        same_annotation_for_both_str.join(["abc"]),
        same_annotation_for_both_converter.exists(),
        optional_value + 1 if optional_value is not None else 0,
        optional_parameter + 1,
        aliased + 1,
        file_opener,
    )


if __name__ == "__main__":
    run(main)
