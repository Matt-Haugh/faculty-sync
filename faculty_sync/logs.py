import logging
import os

import daiquiri

from .dirs import ensure_parent_exists


# The XDG Base Directory Specification does not specify where
# logs generated by a program running as a user should be stored.
# It does specify that 'data' files can be stored in ~/.local.

LOG_LOCATION = os.path.expanduser(
    "~/.local/share/faculty-sync/faculty-sync.log"
)


def setup_logging(debug):
    if debug:
        ensure_parent_exists(LOG_LOCATION)
        daiquiri.setup(
            level=logging.INFO, outputs=[daiquiri.output.File(LOG_LOCATION)]
        )
    else:
        daiquiri.setup(
            level=logging.FATAL, outputs=[daiquiri.output.File("/dev/null")]
        )
