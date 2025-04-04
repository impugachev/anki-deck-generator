# Anki Deck Generator

A tool to automatically generate Anki decks for language learning, with translations, images, and pronunciations.

## Features

- Automatic translation using DeepL API
- Image search for visual associations
- Audio pronunciation using Reverso Voice
- Usage examples from Tatoeba
- Two-way cards (source -> target language and vice versa)

## Installation

```bash
pip install .
```

## Usage

```bash
python -m anki_deck_generator --api-key YOUR_DEEPL_API_KEY \
                            --words-file path/to/words.txt \
                            --source-language Russian \
                            --target-language Dutch \
                            --deck-name "My Language Deck" \
                            -o output_deck.apkg
```

### Arguments

- `--api-key`: DeepL API key (required)
- `--words-file`: Path to a text file with words to learn, one per line (required)
- `--source-language`: Source language (required)
- `--target-language`: Target language (required)
- `--deck-name`: Name of the generated Anki deck (default: "Generated deck")
- `-o, --output`: Output path for the Anki deck (default: deck.apkg)
- `--working-dir`: Working directory for media files (optional)
