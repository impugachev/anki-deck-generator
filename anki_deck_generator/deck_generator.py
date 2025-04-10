import random
import logging
from pathlib import Path
import genanki
from anki_deck_generator.translators.deepl_translator import Translator
from anki_deck_generator.voice.reverso_voice import ReversoVoice
from anki_deck_generator.google_image_downloader import ImageDownloader
from anki_deck_generator.usage_fetcher import UsageExampleFetcher


class AnkiDeckGenerator:
    def __init__(self, deck_name, source_language, target_language, deepl_api_key, working_dir):
        self.deck_name = deck_name
        self.source_language = source_language
        self.target_language = target_language
        self.deepl_api_key = deepl_api_key
        self.working_dir = Path(working_dir)
        self.deck = genanki.Deck(random.randint(1, 2**31 - 1), deck_name)
        self.media = []
        self.model = self._generate_model()

        # Initialize helper classes
        self.translator = Translator(self.deepl_api_key, self.source_language, self.target_language)
        self.reverso_voice = ReversoVoice(self.source_language, self.working_dir)
        self.image_downloader = ImageDownloader(self.working_dir)
        self.usage_fetcher = UsageExampleFetcher(self.source_language, self.target_language)

    def _make_word_dir(self, word):
        (self.working_dir / word).mkdir(parents=True, exist_ok=True)

    def _generate_model(self):
        return genanki.Model(
            random.randint(1, 2**31 - 1),
            'Gen model',
            fields=[
                {'name': self.source_language},
                {'name': self.target_language},
                {'name': 'Image'},
                {'name': 'Sound'},
                {'name': 'Usage'},
            ],
            templates=[
                {
                    'name': f'{self.target_language}+{self.source_language} -> {self.source_language}',
                    'qfmt': f"""
                        <div class="card-header">
                            <h1>{{{{{self.target_language}}}}}</h1>
                        </div>
                        <div class="card-image">
                            {{{{Image}}}}
                        </div>
                        <div class="card-input">
                            {{{{type:{self.source_language}}}}}
                        </div>
                    """,
                    'afmt': """
                        <div class="card-header">
                            <h1>{{FrontSide}}</h1>
                        </div>
                        <hr id="answer">
                        <div class="card-usage">
                            <p>{{Usage}}</p>
                        </div>
                        <div class="card-sound">
                            {{Sound}}
                        </div>
                    """,
                },
                {
                    'name': f'{self.source_language}+{self.target_language} -> {self.target_language}',
                    'qfmt': f"""
                        <div class="card-header">
                            <h1>{{{{{self.source_language}}}}}</h1>
                        </div>
                        <div class="card-sound">
                            {{{{Sound}}}}
                        </div>
                        <div class="card-input">
                            {{{{type:{self.target_language}}}}}
                        </div>
                    """,
                    'afmt': """
                        <div class="card-header">
                            <h1>{{FrontSide}}</h1>
                        </div>
                        <hr id="answer">
                        <div class="card-image">
                            {{Image}}
                        </div>
                        <div class="card-usage">
                            <p>{{Usage}}</p>
                        </div>
                    """,
                },
            ],
            css="""\
.card {
    font-family: 'Arial', sans-serif;
    font-size: 18px;
    text-align: center;
    color: #333;
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.card-header h1 {
    font-size: 24px;
    color: #007BFF;
    margin-bottom: 10px;
}
.card-image img {
    max-width: 100%;
    max-height: 300px;
    object-fit: contain;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin: 10px 0;
}
.card-usage p {
    font-style: italic;
    color: #555;
}
.card-sound {
    margin-top: 10px;
}
.card-input {
    margin-top: 15px;
}
""",
        )

    def _make_note(self, word):
        self._make_word_dir(word)

        translation = self.translator.translate(word)
        usage = self.usage_fetcher.fetch_usage(word)
        sound_file = self.reverso_voice.download_sound(word)
        image_file = self.image_downloader.download_image(word)  # TODO: give a choice to use translation as a query
        if image_file is None:
            image_field = ''
            image_media = []
        else:
            image_field = f'<img src="{image_file.name}">'
            image_media = [image_file]

        note = genanki.Note(
            model=self.model, fields=[word, translation, image_field, f'[sound:{sound_file.name}]', usage]
        )
        return note, [sound_file] + image_media

    def add_word(self, word):
        logging.info(f"Creating a card for the word '{word}'...")
        try:
            note, media_files = self._make_note(word)
            self.deck.add_note(note)
            self.media.extend(media_files)
            logging.info(f"The card for the word '{word}' has been created!")
        except Exception as e:
            logging.error(f"Error creating a card for the word '{word}': {e}")

    def add_words(self, words, skip_empty=True):
        for word in words:
            word = word.strip()
            if word == '':
                if skip_empty:
                    continue
                else:
                    raise ValueError('Empty word found in the list')
            self.add_word(word)

    def save_deck(self, output_path):
        package = genanki.Package(self.deck)
        package.media_files = self.media
        package.write_to_file(output_path)
