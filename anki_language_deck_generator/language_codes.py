LANGUAGES = {
    'Arabic': 'ar',
    'English': 'en',
    'Catalan': 'ca',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'Finnish': 'fi',
    'French': 'fr',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Chinese': 'zh',
    'Norwegian': 'no',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Turkish': 'tr',
}


def get_language_codes(source_language, target_language, languages_dict=LANGUAGES):
    if source_language not in languages_dict:
        raise ValueError(f'Unknown source language: {source_language}')
    if target_language not in languages_dict:
        raise ValueError(f'Unknown target language: {target_language}')
    return languages_dict[source_language], languages_dict[target_language]
