import hwilib.commands
import wallycore as wally

from green_cli.authenticators import *

class HWIDevice(HardwareDevice):

    @staticmethod
    def _path_to_string(path: List[int]) -> str:
        """Return string representation of path for hwi interface

        The gdk passes paths as lists of int, hwi expects strings with '/'s
        >>> _path_to_string([1, 2, 3])
        "m/1/2/3"
        """
        return '/'.join(['m'] + [str(path_elem) for path_elem in path])

    def __init__(self, details: Dict):
        """Create a hardware wallet instance

        details: Details of hardware wallet as returned by hwi enumerate command
        """
        self.details = details
        self._device = hwilib.commands.find_device(details['path'])

    @property
    def name(self) -> str:
        """Return a name for the device, e.g. 'ledger@0001:0007:00'"""
        return '{}@{}'.format(self.details['type'], self.details['path'])

    def get_xpub(self, path: List[int]) -> bytes:
        """Return a base58 encoded xpub

        path: Bip32 path of xpub to return
        """
        path = HWIDevice._path_to_string(path)
        return hwilib.commands.getxpub(self._device, path)['xpub']

    def sign_message(self, path: List[int], message: str) -> bytes:
        """Return der encoded signature of a message

        path: BIP32 path of key to use for signing
        message: Message to be signed
        """
        path = HWIDevice._path_to_string(path)

        click.echo('Signing with hardware device {}'.format(self.name))
        click.echo('Please check the device for interaction')

        signature = hwilib.commands.signmessage(self._device, message, path)['signature']
        return wally.ec_sig_to_der(base64.b64decode(signature)[1:])

    def sign_tx(self, details):
        raise NotImplementedError("hwi sign tx not implemented")

    @staticmethod
    def get_device():
        """Enumerate and select a hardware wallet"""
        devices = hwilib.commands.enumerate()
        logging.debug('hwi devices: %s', devices)

        if len(devices) == 0:
            raise click.ClickException(
                "No hwi devices\n"
                "Check:\n"
                "- A device is attached\n"
                "- udev rules, device drivers, etc.\n"
                "- Cables/connections\n"
                "- The device is enabled, for example by entering a PIN\n")
        if len(devices) > 1:
            raise NotImplementedError("Device selection not implemented")

        device = devices[0]
        logging.debug('hwi device: %s', device)
        if 'error' in device:
            raise click.ClickException(
                "Error with hwi device: {}\n"
                "Check the device and activate the bitcoin app if necessary"
                .format(device['error']))
        return HWIDevice(device)

def get_authenticator(network, config_dir):
    return HWIDevice.get_device()
