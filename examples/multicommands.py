from clize import run


def add(*text):
    """Adds an entry to the to-do list.

    :param text: The text associated with the entry.
    """
    return "OK I will remember that."


def list_():
    """Lists the existing entries."""
    return "Sorry I forgot it all :("


run(add, list_, description="""
    A reliable to-do list utility.

    Store entries at your own risk.
    """)
