from aqt import mw, gui_hooks
from aqt.qt import QAction, qconnect

__version__ = '0.1.0'
__all__ = ['AnkiDeckGenerator']


def show_deck_generator():
    # Import here to avoid circular imports
    from .dialog import DeckGeneratorDialog
    dialog = DeckGeneratorDialog(mw)
    dialog.exec()

def setup_menu():
    action = QAction("Generate Language Learning Deck...", mw)
    qconnect(action.triggered, show_deck_generator)
    mw.form.menuTools.addAction(action)

# Use the new gui_hooks system
gui_hooks.profile_did_open.append(setup_menu)
