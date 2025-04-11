# Anki Deck Generator

A tool to automatically generate Anki decks for language learning, with translations, images, and pronunciations.

## Features

- Automatic translation using DeepL API
- Image search for visual associations
- Audio pronunciation using Reverso Voice
- Usage examples from Tatoeba
- Two-way cards (source -> target language and vice versa)
- Can be used as both a standalone tool and an Anki addon

## Installation

### As a standalone tool:
```bash
pip install .
```

### As an Anki addon:
1. Open Anki
2. Go to Tools -> Add-ons
3. Click "Get Add-ons..."
4. Enter the addon code: [To be added after publishing]
5. Restart Anki

## Usage

### Standalone tool:
```bash
python -m anki_deck_generator --words-file path/to/words.txt \
                            --source-language Russian \
                            --target-language Dutch \
                            --deck-name "My Language Deck" \
                            -o output_deck.apkg
```

### As an Anki addon:
1. Open Anki
2. Go to Tools -> Generate Language Learning Deck...
3. Select source and target languages
4. Enter your word list (one word per line)
5. Click "Generate Deck"

### Arguments (Standalone mode)

- `--words-file`: Path to a text file with words to learn, one per line (required)
- `--source-language`: Source language (required)
- `--target-language`: Target language (required)
- `--deck-name`: Name of the generated Anki deck (default: "Generated deck")
- `-o, --output`: Output path for the Anki deck (default: deck.apkg)
- `--working-dir`: Working directory for media files (optional)
