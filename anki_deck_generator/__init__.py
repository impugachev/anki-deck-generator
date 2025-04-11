from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect
from anki.hooks import addHook
from anki_deck_generator.deck_generator import AnkiDeckGenerator
from anki_deck_generator.dialog import DeckGeneratorDialog

__version__ = '0.1.0'
__all__ = ['AnkiDeckGenerator']


def show_deck_generator():
    dialog = DeckGeneratorDialog(mw)
    dialog.exec_()


def setup_menu():
    action = QAction("Generate Language Learning Deck...", mw)
    qconnect(action.triggered, show_deck_generator)
    mw.form.menuTools.addAction(action)


addHook("profileLoaded", setup_menu)
