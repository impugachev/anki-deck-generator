from aqt import mw, gui_hooks
from aqt.qt import QAction, qconnect

def show_deck_generator():
    # Import here to avoid circular imports
    from anki_language_deck_generator.dialog import DeckGeneratorDialog
    dialog = DeckGeneratorDialog(mw)
    dialog.exec()

def setup_menu():
    action = QAction("Generate Language Learning Deck...", mw)
    qconnect(action.triggered, show_deck_generator)
    mw.form.menuTools.addAction(action)

# Use the new gui_hooks system
gui_hooks.profile_did_open.append(setup_menu)
