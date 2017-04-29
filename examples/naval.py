"""
Naval battle example from docopt
"""


from collections import OrderedDict
from clize import run, parser


def ship_new(name):
    """Create a new ship

    name: The name to attribute to the ship
    """
    return "Created ship {0}".format(name)


knots = parser.value_converter(float, name='KN')


def ship_move(ship, x:float, y:float, *, speed:knots=10):
    """Move a ship

    ship: The ship which to move

    x: X coordinate

    y: Y coordinate

    speed: Speed in knots
    """
    return "Moving ship {0} to {1},{2} with speed {3}".format(ship, x, y, speed)


def ship_shoot(ship, x:float, y:float):
    """Make a ship fire at the designated coordinates

    ship: The ship which to move

    x: X coordinate

    y: Y coordinate
    """
    return "{0} shoots at {1},{2}".format(ship, x, y)


def mine_set(x, y, *, drifting=False):
    """Set a mine

    x: X coordinate

    y: Y coordinate

    drifting: Don't anchor the mine and let it drift
    """
    return "Set {0} mine at {1},{2}".format(
        "drifting" if drifting else "anchored",
        x, y)


def mine_remove(x, y):
    """Removes a mine

    x: X coordinate

    y: Y coordinate
    """
    return "Removing mine at {0}, {1}".format(x, y)


def version():
    return "Version 1.0"


run({
        'ship': OrderedDict([
            ('new', ship_new),
            ('move', ship_move),
            ('shoot', ship_shoot),
        ]),
        'mine': OrderedDict([
            ('set', mine_set),
            ('remove', mine_remove),
        ]),
    }, alt=version)
