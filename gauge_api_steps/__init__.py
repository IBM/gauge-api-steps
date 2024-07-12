#
# Copyright IBM Corp. 2019-
# SPDX-License-Identifier: MIT
#

from .reporting import mask_secrets

class MaskedAssertionError(AssertionError):
    """ Make sure that secrets are masked whenever an assertion fails by overwriting AssertionError. """
    def __init__(self, msg):
        super().__init__(mask_secrets(msg))

__builtins__['AssertionError'] = MaskedAssertionError
