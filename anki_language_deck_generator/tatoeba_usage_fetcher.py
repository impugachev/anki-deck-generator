from urllib.parse import urlencode
import requests
from anki_language_deck_generator.language_codes import get_language_codes


class UsageExampleFetcher:
    TATOEBA_URL = 'https://tatoeba.org/ru/api_v0/search'
    LANGUAGES = {
        'Arabic': 'ara',
        'English': 'eng',
        'Catalan': 'cat',
        'Czech': 'ces',
        'Danish': 'dan',
        'Dutch': 'nld',
        'Finnish': 'fin',
        'French': 'fra',
        'German': 'deu',
        'Greek': 'ell',
        'Hebrew': 'heb',
        'Italian': 'ita',
        'Japanese': 'jpn',
        'Korean': 'kor',
        'Chinese': 'cmn',
        'Norwegian': 'nno',
        'Polish': 'pol',
        'Portuguese': 'por',
        'Romanian': 'ron',
        'Russian': 'rus',
        'Spanish': 'spa',
        'Swedish': 'swe',
        'Turkish': 'tur'
    }

    def __init__(self, source_language, target_language):
        self.source_language, self.target_language = get_language_codes(
            source_language, target_language, self.LANGUAGES
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
            'query': word,
            'sort': 'relevance',
            'orphans': 'no',
            'unapproved': 'no',
            'trans_filter': 'limit',
            'trans_to': 'rus',
            'word_count_min': '5',
            'word_count_max': '10',
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
            result.append(f"<b>{usages[i]['text']}</b>")
            result.append(self._get_usage_translation(usages[i]))

        return '<br>'.join(result)
