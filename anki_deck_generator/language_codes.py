LANGUAGES = {
    'Russian': 'ru',
    'Dutch': 'nl',
    'Georgian': 'ka',
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Chinese': 'zh',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Arabic': 'ar',
    'Hindi': 'hi',
    'Turkish': 'tr',
    'Polish': 'pl',
    'Swedish': 'sv',
}


def get_language_codes(source_language, target_language, languages_dict=LANGUAGES):
    if source_language not in languages_dict:
        raise ValueError(f'Unknown source language: {source_language}')
    if target_language not in languages_dict:
        raise ValueError(f'Unknown target language: {target_language}')
    return languages_dict[source_language], languages_dict[target_language]
