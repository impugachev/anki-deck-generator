from urllib.parse import urlencode
import requests
from anki_deck_generator.utils.language_codes import get_language_codes


class UsageExampleFetcher:
    TATOEBA_URL = 'https://tatoeba.org/ru/api_v0/search'
    LANGUAGES = {
        'English': 'eng',
        'Russian': 'rus',
        'Dutch': 'nld',
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
            'query': word,
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
            result.append(f'<b>{usages[i]['text']}</b>')
            result.append(self._get_usage_translation(usages[i]))

        return '<br>'.join(result)
