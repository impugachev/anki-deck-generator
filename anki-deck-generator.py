import argparse
import base64
import logging
import random
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

import deepl
import genanki
import requests
from icrawler.builtin import GoogleImageCrawler


def get_language_codes(languages_dict, source_language, target_language):
    if source_language not in languages_dict:
        raise ValueError(f'Unknown source language: {source_language}')
    if target_language not in languages_dict:
        raise ValueError(f'Unknown target language: {target_language}')
    return languages_dict[source_language], languages_dict[target_language]


class Translator:
    LANGUAGES = {
        'Russian': 'RU',
        'Dutch': 'NL',
    }

    def __init__(self, api_key, source_language, target_language):
        self.translator = deepl.Translator(api_key)
        self.source_language, self.target_language = get_language_codes(
            self.LANGUAGES, source_language, target_language
        )

    def translate(self, word):
        result = self.translator.translate_text(
            word,
            source_lang=self.source_language,
            target_lang=self.target_language
        )
        return result.text


class ImageDownloader:
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.crawler = GoogleImageCrawler(storage={'root_dir': working_dir}, log_level=logging.ERROR)

    def download_image(self, word):
        for _ in range(5):
            try:
                self.crawler.crawl(keyword=word, max_num=1, overwrite=True)
                break
            except Exception:
                time.sleep(1)
                continue
        else:
            logging.error(f"Cannot find an image for the word '{word}'")
            return None
        image_file = next(self.working_dir.glob('000001.*'))
        new_name = self.working_dir / word / f'{word}{image_file.suffix}'
        image_file.rename(new_name)
        return new_name


class ReversoVoice:
    VOICE_STREAM_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=xml/GetVoiceStream'
    AVAILABLE_VOICES_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=json/GetAvailableVoices'

    def __init__(self, language, working_dir):
        self.working_dir = working_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            )
        })
        self.voice_name = self._get_voice_for_language(language)

    def _make_voice_url(self, word):
        voice_name_param = {
            'voiceName': self.voice_name
        }
        query_params = {
            'inputText': base64.b64encode(word.encode('utf-8')).decode('utf-8'),
            'voiceSpeed': 100,
            'mp3BitRate': 128
        }
        return f'{self.VOICE_STREAM_URL}/{urlencode(voice_name_param)}?{urlencode(query_params)}'

    def _get_voice_for_language(self, language):
        response = self.session.get(self.AVAILABLE_VOICES_URL)
        if response.status_code != 200:
            raise Exception(f'Failed to get available voices: {response.status_code}')
        voices = response.json()['Voices']
        voice = next((v for v in voices if v['Language'] == language), None)
        if voice is None:
            raise Exception(f'No voice found for language: {language}')
        return voice['Name']

    def download_sound(self, word):
        sound_url = self._make_voice_url(word)
        sound_file_path = self.working_dir / word / f'{word}.mp3'
        response = self.session.get(sound_url)
        if response.status_code != 200:
            raise Exception(f'Failed to get sound: {response.status_code}')
        with sound_file_path.open('wb') as sound_file:
            sound_file.write(response.content)
        return sound_file_path


class UsageExampleFetcher:
    TATOEBA_URL = 'https://tatoeba.org/ru/api_v0/search'
    LANGUAGES = {
        'English': 'eng',
        'Russian': 'rus',
        'Dutch': 'nld'
    }

    def __init__(self, source_language, target_language):
        self.source_language, self.target_language = get_language_codes(
            self.LANGUAGES, source_language, target_language
        )
        self.session = requests.Session()

    def _get_usage_translation(self, usage):
        for translation_array in usage['translations']:
            for translation in translation_array:
                return translation['text']

    def fetch_usage(self, word):
        params = {
            'from': self.source_language,
            'to': self.target_language,
            'query': word
        }
        url = f'{self.TATOEBA_URL}?{urlencode(params)}'

        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f'Failed to get usage examples: {response.status_code}')
        usages = response.json()['results']
        result = []
        for i in range(2):
            if i >= len(usages):
                break
            result.append(f'<b>{usages[i]["text"]}</b>')
            result.append(self._get_usage_translation(usages[i]))

        return '<br>'.join(result)


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
                {'name': 'Usage'}
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
                            <input type="text" style="width: 80%; padding: 5px; font-size: 16px;">
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
                            <input type="text" style="width: 80%; padding: 5px; font-size: 16px;">
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
"""
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
            model=self.model,
            fields=[word, translation, image_field, f'[sound:{sound_file.name}]', usage]
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


parser = argparse.ArgumentParser(
    prog='anki-deck-generator',
    description='Generate simple Anki deck from list of words')
parser.add_argument('--deck-name', default='Generated deck', help='Name of the Anki deck')
parser.add_argument('--api-key', required=True, help='DeepL API key')
parser.add_argument('--words-file', required=True, help='Path to the file with words, one word per line')
parser.add_argument('--source-language', required=True, help='Source language')
parser.add_argument('--target-language', required=True, help='Target language')
parser.add_argument('-o', '--output', default='deck.apkg', help='Output path for the Anki deck')
parser.add_argument('--working-dir', help='Working directory for media files')
args = parser.parse_args()

if args.working_dir:
    working_dir = args.working_dir
else:
    temp_dir = tempfile.TemporaryDirectory()
    working_dir = temp_dir.name

logging.basicConfig(level=logging.INFO)  # TODO: make it better
deck_generator = AnkiDeckGenerator(
    deck_name=args.deck_name,
    source_language=args.source_language,
    target_language=args.target_language,
    deepl_api_key=args.api_key,
    working_dir=working_dir
)
words = []
with open(args.words_file, 'r', encoding='UTF-8') as f:
    words = f.readlines()
deck_generator.add_words(words)
deck_generator.save_deck(args.output)

if not args.working_dir:
    temp_dir.cleanup()  # Clean up the temporary directory if it was used
