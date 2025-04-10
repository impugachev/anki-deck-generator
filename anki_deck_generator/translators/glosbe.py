import requests
from bs4 import BeautifulSoup

from anki_deck_generator.language_codes import get_language_codes


class Translator:
    def __init__(self, source_language, target_language):
        source_language_code, target_language_code = get_language_codes(
            source_language, target_language
        )
        self.base_url = '/'.join(
            ['https://glosbe.com', source_language_code, target_language_code]
        )

    def translate(self, word):
        response = requests.get(f'{self.base_url}/{word}')
        response.raise_for_status()

        # Parse HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find content summary paragraph
        summary_paragraph = soup.find('p', id='content-summary')
        if summary_paragraph is None:
            raise RuntimeError(f"Cannot find content summary for word '{word}'")

        # Find translations in strong tags
        translations = summary_paragraph.find('strong')
        if translations is None:
            raise RuntimeError(f"Cannot find translations for word '{word}'")

        # Extract and split translations
        return translations.text.split(", ")[0]
