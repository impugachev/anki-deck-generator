from pathlib import Path
import logging

from gtts import gTTS
from gtts import lang as gtts_lang

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleVoice:
    """
    A class to handle voice synthesis using the gTTS (Google Text-to-Speech) library.
    This class now provides methods to download sound files for given words
    in a specified language by utilizing Google's online Text-to-Speech API,
    making it platform-independent regarding voice management.

    NOTE: This library requires an active internet connection to synthesize speech.
    """
    # These URLs are no longer used as we are using gTTS, but kept for context.
    VOICE_STREAM_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=xml/GetVoiceStream'
    AVAILABLE_VOICES_URL = 'https://voice.reverso.net/RestPronunciation.svc/v1/output=json/GetAvailableVoices'

    # Language aliases for convenience. These now map to gTTS-compatible language codes (ISO 639-1).
    # gTTS typically uses two-letter language codes.
    # This dictionary is now dynamically populated to include all languages supported by gTTS.
    LANGUAGE_ALIASES = {}
    try:
        # Dynamically populate LANGUAGE_ALIASES with all gTTS supported languages
        # This makes the class more robust to gTTS updates and covers more languages.
        for code, name in gtts_lang.tts_langs().items():
            # Add both the full name (capitalized) and the code itself as a potential alias.
            # Prioritize more common names for easier use.
            # Handle specific cases for Chinese variants if gTTS uses distinct codes for them.
            if code == 'zh-cn': # Simplified Chinese
                LANGUAGE_ALIASES['Chinese (Mandarin)'] = 'zh-CN'
                LANGUAGE_ALIASES['Mandarin Chinese'] = 'zh-CN'
                LANGUAGE_ALIASES['Chinese'] = 'zh-CN' # Common alias for Mandarin
            elif code == 'zh-tw': # Traditional Chinese
                LANGUAGE_ALIASES['Chinese (Taiwan)'] = 'zh-TW'
            else:
                LANGUAGE_ALIASES[name.capitalize()] = code
                LANGUAGE_ALIASES[code] = code # Allow using the code directly

        # Add some common specific English variants if gTTS supports them distinctly or if preferred
        if 'en' in LANGUAGE_ALIASES.values():
            LANGUAGE_ALIASES['English (US)'] = 'en'
            LANGUAGE_ALIASES['English (UK)'] = 'en' # gTTS 'en' often covers various English accents
            LANGUAGE_ALIASES['American English'] = 'en'
            LANGUAGE_ALIASES['British English'] = 'en'

    except Exception as e:
        logging.warning(f"Could not dynamically load gTTS languages. Using fallback aliases. Error: {e}")
        # Fallback aliases if gtts_lang.tts_langs() fails (e.g., no internet on startup)
        LANGUAGE_ALIASES = {
            'English': 'en',
            'Chinese': 'zh-CN',
            'French': 'fr',
            'Dutch': 'nl',
            'German': 'de',
            'Spanish': 'es',
            'Italian': 'it',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Russian': 'ru',
            'Arabic': 'ar',
            'Portuguese': 'pt',
            'Hindi': 'hi',
            'Turkish': 'tr',
            'Swedish': 'sv',
            'Polish': 'pl',
            'Danish': 'da',
            'Finnish': 'fi',
            'Greek': 'el',
            'Vietnamese': 'vi',
            'Thai': 'th',
            'Indonesian': 'id',
            'Malay': 'ms',
            'Filipino': 'fil',
            'Bengali': 'bn',
            'Gujarati': 'gu',
            'Kannada': 'kn',
            'Malayalam': 'ml',
            'Marathi': 'mr',
            'Tamil': 'ta',
            'Telugu': 'te',
            'Ukrainian': 'uk',
            'Czech': 'cs',
            'Hungarian': 'hu',
            'Romanian': 'ro',
            'Slovak': 'sk',
            'Norwegian': 'no',
            'Hebrew': 'iw', # gTTS uses 'iw' for Hebrew
            'Urdu': 'ur',
            'Nepali': 'ne',
            'Sinhala': 'si',
            'Khmer': 'km',
            'Lao': 'lo',
            'Myanmar (Burmese)': 'my',
            'Amharic': 'am',
            'Swahili': 'sw',
            'Afrikaans': 'af',
            'Catalan': 'ca',
            'Croatian': 'hr',
            'Estonian': 'et',
            'Icelandic': 'is',
            'Latvian': 'lv',
            'Lithuanian': 'lt',
            'Serbian': 'sr',
            'Slovenian': 'sl',
            'Bosnian': 'bs',
            'Azerbaijani': 'az',
            'Georgian': 'ka',
            'Armenian': 'hy',
            'Albanian': 'sq',
            'Macedonian': 'mk',
            'Mongolian': 'mn',
            'Pashto': 'ps',
            'Persian': 'fa',
            'Somali': 'so',
            'Uzbek': 'uz',
            'Zulu': 'zu',
        }


    def __init__(self, language: str, working_dir: str):
        """
        Initializes the ReversoVoice handler using the gTTS engine.

        Args:
            language (str): The desired language for voice synthesis (e.g., 'English', 'French').
                            This will be used to select a matching voice from gTTS.
            working_dir (str): The directory where sound files will be saved.
        """
        self.working_dir = Path(working_dir)
        # Ensure the working directory exists
        self.working_dir.mkdir(parents=True, exist_ok=True)

        logging.info("Initializing gTTS engine...")
        # gTTS doesn't require explicit initialization like pyttsx3.
        # Its 'engine' is essentially the gTTS function itself.
        logging.info("gTTS is ready to use.")

        logging.info(f"ReversoVoice initialized for language: {language}, working directory: {self.working_dir.resolve()}")
        # We store the gTTS-compatible language code directly.
        self.gtts_language_code = self._get_gtts_language_code(language)
        if self.gtts_language_code:
            logging.info(f"Using gTTS language code: '{self.gtts_language_code}' for requested language: {language}")
        else:
            logging.warning(f"No specific gTTS language code found for '{language}'. Will attempt with default 'en'.")
            self.gtts_language_code = 'en' # Fallback to English if no mapping found

    def _get_gtts_language_code(self, language: str) -> str:
        """
        Translates the given language string into a gTTS-compatible language code.

        Args:
            language (str): The desired language (e.g., 'English', 'Dutch').

        Returns:
            str: The gTTS-compatible language code (e.g., 'en', 'nl'), or the original
                 language string if no alias is found (gTTS might still support it directly).
        """
        # Get the standard language code from aliases, or use the language directly
        # gTTS primarily uses ISO 639-1 codes (e.g., 'en', 'fr', 'nl')
        # Some languages might have specific variants like 'zh-CN'.
        # Convert the input language to title case to match the common names from gtts_lang.tts_langs()
        # Also check for lower case codes directly.
        return self.LANGUAGE_ALIASES.get(language, self.LANGUAGE_ALIASES.get(language.capitalize(), self.LANGUAGE_ALIASES.get(language.lower(), None))) or language.lower()

    # The _make_voice_url method is no longer needed for gTTS as it doesn't use URLs this way.
    # It's commented out for clarity.
    # def _make_voice_url(self, word: str) -> str:
    #     """
    #     This method is not used by gTTS.
    #     """
    #     pass


    def download_sound(self, word: str) -> Path:
        """
        Synthesizes the given word into a sound file (MP3) using gTTS.

        Args:
            word (str): The word or phrase to synthesize.

        Returns:
            Path: The file path where the downloaded MP3 sound file is saved.

        Raises:
            Exception: If there's an error during speech synthesis (e.g., network issue).
        """
        # Create a subdirectory for each word to organize the downloaded sound files.
        word_dir = self.working_dir / word
        word_dir.mkdir(parents=True, exist_ok=True)
        sound_file_path = word_dir / f'{word}.mp3'

        logging.info(f"Synthesizing sound for '{word}' in language '{self.gtts_language_code}' and saving to: {sound_file_path}")
        try:
            # Create a gTTS object. 'lang' is the language code.
            # 'slow=False' makes the speech faster.
            tts = gTTS(text=word, lang=self.gtts_language_code, slow=False)

            # Save the audio directly to a file.
            tts.save(str(sound_file_path))
            logging.info(f"Successfully synthesized and saved sound to: {sound_file_path}")
            return sound_file_path
        except Exception as e:
            logging.error(f"Error synthesizing sound for '{word}': {e}")
            logging.error("This usually indicates a network issue or an unsupported language/voice by gTTS.")
            raise # Re-raise the exception for upstream handling

