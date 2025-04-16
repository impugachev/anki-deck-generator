import sys
import platform
from pathlib import Path


def _get_architecture():
    bit, system = platform.architecture()
    if system == 'WindowsPE':
        if bit == '64bit':
            return 'win_amd64'
        elif bit == '32bit':
            return 'win32'
        else:
            raise Exception(f'Unsupported platform: {system} {bit}')
    else:
        raise Exception(f'Unsupported platform: {system} {bit}')


def _setup_path():
    addon_dir = Path(__file__).parent
    sys.path.append(str(addon_dir))
    sys.path.insert(0, str(addon_dir / 'dependencies'))
    sys.path.insert(0, str(addon_dir / 'dependencies' / 'platform' / _get_architecture()))


_setup_path()

from bs4.builder import register_treebuilders_from, _lxml
register_treebuilders_from(_lxml)

from . import anki_deck_generator
