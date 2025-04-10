import deepl
from language_codes import get_language_codes


class Translator:
    def __init__(self, api_key, source_language, target_language):
        self.translator = deepl.Translator(api_key)
        self.source_language, self.target_language = get_language_codes(
            source_language, target_language
        )

    def translate(self, word):
        result = self.translator.translate_text(
            word, source_lang=self.source_language, target_lang=self.target_language
        )
        return result.text
