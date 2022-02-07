from functools import partial
from clize import run
from sigtools.wrappers import decorator
from sigtools import specifiers
import trio


@decorator
def with_trio_event_loop(wrapped, *args, **kwargs):
    return trio.run(partial(wrapped, *args, **kwargs))


@decorator
def with_config(wrapped, *args, setting="abc", **kwargs):
    """
    :param setting: sets a setting
    """
    config = {
        "setting": setting
    }
    return wrapped(*args, config=config, **kwargs)


@decorator
async def with_client(wrapped, *args, timeout=30, **kwargs):
    """
    :param timeout: timeout in seconds
    """
    client = {}
    return wrapped(*args, client=client, **kwargs)


@with_client
@with_config
async def main(*, sleep_for: int, client, config):
    """
    Main description

    :param sleep_for: sleep for this long
    """
    await trio.sleep(sleep_for)


if __name__ == "__main__":
    run(with_trio_event_loop(main))
