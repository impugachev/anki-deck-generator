import sys
from os.path import dirname

sys.path.append(dirname(__file__))
sys.path.insert(0, dirname(__file__) + '/dependencies')

from . import anki_deck_generator
