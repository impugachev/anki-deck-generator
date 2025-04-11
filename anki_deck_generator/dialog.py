from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QLineEdit, QProgressBar
)
from aqt.utils import showInfo
from anki.utils import int_time
from anki.collection import ImportAnkiPackageRequest, ImportAnkiPackageOptions
from anki.import_export_pb2 import ImportAnkiPackageUpdateCondition
from anki_deck_generator.language_codes import LANGUAGES
from anki_deck_generator.deck_generator import AnkiDeckGenerator
import tempfile
import os


class DeckGeneratorDialog(QDialog):
    def __init__(self, mw):
        super().__init__(parent=mw)
        self.mw = mw
        self.config = self._load_config()
        self.setup_ui()

    def _load_config(self):
        # Get addon dir name/path
        addon_dir = os.path.dirname(os.path.dirname(__file__))
        # Default config
        config = {
            'default_source_language': 'Dutch',
            'default_target_language': 'Russian',
            'default_deck_name': 'Generated Language Deck'
        }
        # Try to load from config.json
        config_path = os.path.join(addon_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import json
                    loaded_config = json.load(f)
                    config.update(loaded_config)
            except Exception as e:
                showInfo(f"Error loading config: {str(e)}")
        return config

    def setup_ui(self):
        self.setWindowTitle("Language Deck Generator")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Source Language
        source_layout = QHBoxLayout()
        source_label = QLabel("Source Language:")
        self.source_combo = QComboBox()
        self.source_combo.addItems(sorted(LANGUAGES.keys()))
        default_source = self.config.get('default_source_language', 'Dutch')
        self.source_combo.setCurrentText(default_source)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)

        # Target Language
        target_layout = QHBoxLayout()
        target_label = QLabel("Target Language:")
        self.target_combo = QComboBox()
        self.target_combo.addItems(sorted(LANGUAGES.keys()))
        default_target = self.config.get('default_target_language', 'Russian')
        self.target_combo.setCurrentText(default_target)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        layout.addLayout(target_layout)

        # Deck Name
        deck_layout = QHBoxLayout()
        deck_label = QLabel("Deck Name:")
        self.deck_name = QLineEdit()
        default_deck = self.config.get('default_deck_name', 'Generated Language Deck')
        self.deck_name.setText(default_deck)
        deck_layout.addWidget(deck_label)
        deck_layout.addWidget(self.deck_name)
        layout.addLayout(deck_layout)

        # Words Input
        words_label = QLabel("Enter words (one per line):")
        layout.addWidget(words_label)
        self.words_text = QTextEdit()
        layout.addWidget(self.words_text)

        # Progress Bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Buttons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        self.generate_btn = QPushButton("Generate Deck")
        self.generate_btn.clicked.connect(self.generate_deck)
        self.generate_btn.setDefault(True)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.generate_btn)
        layout.addLayout(buttons_layout)

    def update_progress(self, current, total):
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"Processing word {current} of {total} ({percentage}%)")

    def generate_deck(self):
        source_language = self.source_combo.currentText()
        target_language = self.target_combo.currentText()
        deck_name = self.deck_name.text()
        words = [w for w in self.words_text.toPlainText().split('\n') if w.strip()]

        if not words:
            showInfo("Please enter at least one word")
            return

        # Show progress bar and disable generate button
        self.progress_bar.show()
        self.generate_btn.setEnabled(False)

        # Create temporary directory for media files
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                generator = AnkiDeckGenerator(
                    deck_name=deck_name,
                    source_language=source_language,
                    target_language=target_language,
                    working_dir=temp_dir,
                    progress_callback=self.update_progress
                )

                generator.add_words(words)
                
                # Save to a temporary file
                temp_deck = os.path.join(temp_dir, f"temp_deck_{int_time()}.apkg")
                generator.save_deck(temp_deck)
                
                # Import into Anki
                self.mw.col.import_anki_package(
                    ImportAnkiPackageRequest(
                        package_path=temp_deck,
                        options=ImportAnkiPackageOptions(
                            update_notes=ImportAnkiPackageUpdateCondition.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER,
                            update_notetypes=ImportAnkiPackageUpdateCondition.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER,
                        )
                    )
                )
                self.mw.deckBrowser.refresh()
                showInfo("Deck generated and imported successfully!")
                self.accept()
                
            except Exception as e:
                showInfo(f"Error generating deck: {str(e)}")
            finally:
                # Re-enable generate button and hide progress bar
                self.generate_btn.setEnabled(True)
                self.progress_bar.hide()
