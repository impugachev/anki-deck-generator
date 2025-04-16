import base64
from pathlib import Path
from urllib.parse import urlencode
import requests


class ReversoVoice:
    """
    A class to handle voice synthesis using Reverso API.
    This class provides methods to download sound files for given words
    in a specified language using the Reverso API.
    """
    VOICE_STREAM_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=xml/GetVoiceStream'
    AVAILABLE_VOICES_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=json/GetAvailableVoices'
    LANGUAGE_ALIASES = {
        'English': 'British',
        'Chinese': 'Mandarin Chinese',
    }

    def __init__(self, language, working_dir):
        self.working_dir = Path(working_dir)
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                )
            }
        )
        self.voice_name = self._get_voice_for_language(language)

    def _make_voice_url(self, word):
        voice_name_param = {'voiceName': self.voice_name}
        query_params = {
            'inputText': base64.b64encode(word.encode('utf-8')).decode('utf-8'),
            'voiceSpeed': 100,
            'mp3BitRate': 128,
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
