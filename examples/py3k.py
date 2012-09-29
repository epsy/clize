#!/usr/bin/env python
from clize import clize, run

@clize
def connect(
        host,
        port=400,
        *,
        number: 'n' = 1.2,
        negative: 'm' = False
        ):
    """
    If this thing did anything it would connect to host and
    send the float described by number.

    host: The host to connect to

    port: The port to connect to

    number: The number to send

    negative: Multiply number by -1?

    """
    print(
        "I would connect to {0}:{1} and send {2} but I'm just an example!"
            .format(host, port, -number if negative else number)
        )

if __name__ == '__main__':
    run(connect)
