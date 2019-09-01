# clize -- A command-line argument parser for Python
# Copyright (C) 2011-2016 by Yann Kaiser and contributors. See AUTHORS and
# COPYING for details.

import sys
import warnings


__all__ = []


if sys.argv and "test" in sys.argv[0]:
    warnings.filterwarnings("default")
    warnings.filterwarnings("error", module="clize")
    warnings.filterwarnings("error", module=".*/clize/")
