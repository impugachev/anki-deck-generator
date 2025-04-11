from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QLineEdit, QCheckBox
)
from aqt.utils import showInfo
from aqt.mw import addonManager
from anki.lang import _
from .language_codes import LANGUAGES
from .deck_generator import AnkiDeckGenerator
import tempfile
import os


class DeckGeneratorDialog(QDialog):
    def __init__(self, mw):
        super().__init__(mw)
        self.mw = mw
        self.config = self.load_config()
        self.setup_ui()

    def load_config(self):
        return addonManager.getConfig(__name__)

    def setup_ui(self):
        self.setWindowTitle(_("Language Deck Generator"))
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Source Language
        source_layout = QHBoxLayout()
        source_label = QLabel(_("Source Language:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(sorted(LANGUAGES.keys()))
        default_source = self.config.get('default_source_language', 'English')
        self.source_combo.setCurrentText(default_source)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)

        # Target Language
        target_layout = QHBoxLayout()
        target_label = QLabel(_("Target Language:"))
        self.target_combo = QComboBox()
        self.target_combo.addItems(sorted(LANGUAGES.keys()))
        default_target = self.config.get('default_target_language', 'Russian')
        self.target_combo.setCurrentText(default_target)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        layout.addLayout(target_layout)

        # Deck Name
        deck_layout = QHBoxLayout()
        deck_label = QLabel(_("Deck Name:"))
        self.deck_name = QLineEdit()
        default_deck = self.config.get('default_deck_name', 'Generated Language Deck')
        self.deck_name.setText(default_deck)
        deck_layout.addWidget(deck_label)
        deck_layout.addWidget(self.deck_name)
        layout.addLayout(deck_layout)

        # Options
        options_layout = QVBoxLayout()
        self.use_images = QCheckBox(_("Include Images"))
        self.use_audio = QCheckBox(_("Include Audio"))
        self.use_examples = QCheckBox(_("Include Usage Examples"))
        
        self.use_images.setChecked(self.config.get('use_images', True))
        self.use_audio.setChecked(self.config.get('use_audio', True))
        self.use_examples.setChecked(self.config.get('use_examples', True))
        
        options_layout.addWidget(self.use_images)
        options_layout.addWidget(self.use_audio)
        options_layout.addWidget(self.use_examples)
        layout.addLayout(options_layout)

        # Words Input
        words_label = QLabel(_("Enter words (one per line):"))
        layout.addWidget(words_label)
        self.words_text = QTextEdit()
        layout.addWidget(self.words_text)

        # Buttons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        generate_btn = QPushButton(_("Generate Deck"))
        generate_btn.clicked.connect(self.generate_deck)
        generate_btn.setDefault(True)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(generate_btn)
        layout.addLayout(buttons_layout)

    def generate_deck(self):
        source_language = self.source_combo.currentText()
        target_language = self.target_combo.currentText()
        deck_name = self.deck_name.text()
        words = self.words_text.toPlainText().split('\n')

        if not words or not ''.join(words).strip():
            showInfo(_("Please enter at least one word"))
            return

        # Create temporary directory for media files
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                generator = AnkiDeckGenerator(
                    deck_name=deck_name,
                    source_language=source_language,
                    target_language=target_language,
                    working_dir=temp_dir
                )

                # Apply settings
                generator.use_images = self.use_images.isChecked()
                generator.use_audio = self.use_audio.isChecked()
                generator.use_examples = self.use_examples.isChecked()

                generator.add_words(words)
                
                # Save to a temporary file
                temp_deck = os.path.join(temp_dir, "temp_deck.apkg")
                generator.save_deck(temp_deck)
                
                # Import into Anki
                self.mw.handleImport(temp_deck)
                showInfo(_("Deck generated and imported successfully!"))
                self.accept()
                
            except Exception as e:
                showInfo(_("Error generating deck: %s") % str(e))
