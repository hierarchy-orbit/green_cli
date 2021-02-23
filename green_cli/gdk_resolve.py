import json
import logging

from typing import Dict, List

import greenaddress as gdk

from . import context

class TwoFactorResolver:
    """Resolves two factor authentication via the console"""

    @staticmethod
    def select_auth_factor(factors: List[str]) -> str:
        """Given a list of auth factors prompt the user to select one and return it"""
        if len(factors) > 1:
            for i, factor in enumerate(factors):
                print("{}) {}".format(i, factor))
            return factors[int(input("Select factor: "))]
        return factors[0]

    @staticmethod
    def resolve(details: Dict[str, str]):
        """Prompt the user for a 2fa code"""
        if details['method'] == 'gauth':
            msg = "Enter Google Authenticator 2fa code for action '{}': ".format(details['action'])
        else:
            msg = "Enter 2fa code for action '{}' sent by {} ({} attempts remaining): ".format(
                details['action'], details['method'], details['attempts_remaining'])
        return input(msg)


def gdk_resolve(auth_handler):
    """Resolve a GA_auth_handler

    GA_auth_handler instances are returned by some gdk functions. They represent a state machine
    that drives the process of interacting with the user for two factor authentication or
    authentication using some external (hardware) device.
    """
    while True:
        status = gdk.auth_handler_get_status(auth_handler)
        status = json.loads(status)
        logging.debug('auth handler status = %s', status)
        state = status['status']
        logging.debug('auth handler state = %s', state)
        if state == 'error':
            raise RuntimeError(status)
        if state == 'done':
            logging.debug('auth handler returning done')
            return status['result']
        if state == 'request_code':
            # request_code only applies to 2fa requests
            authentication_factor = TwoFactorResolver.select_auth_factor(status['methods'])
            logging.debug('requesting code for %s', authentication_factor)
            gdk.auth_handler_request_code(auth_handler, authentication_factor)
        elif state == 'resolve_code':
            # resolve_code covers two different cases: a request for authentication data from some
            # kind of authentication device, for example a hardware wallet (but could be some
            # software implementation) or a 2fa request
            if status['device']:
                logging.debug('resolving auth handler with authentication device')
                resolution = context.authenticator.resolve(status)
            else:
                logging.debug('resolving two factor authentication')
                resolution = TwoFactorResolver.resolve(status)
            logging.debug('auth handler resolved: %s', resolution)
            gdk.auth_handler_resolve_code(auth_handler, resolution)
        elif state == 'call':
            gdk.auth_handler_call(auth_handler)


