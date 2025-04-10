from pathlib import Path
import xml.etree.ElementTree as ET
import requests


class WordNotFoundError(Exception):
    pass


class NoNederlandsSectionError(Exception):
    pass


class DutchWiktionaryWord:
    def __init__(self, word, working_dir):
        self.working_dir = Path(working_dir)
        self.word = word
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                )
            }
        )
        response = self.session.get(
            f'https://nl.wiktionary.org/w/api.php'
            f'?action=parse&format=json&prop=text%7Clanglinks'
            f'&formatversion=2&utf8=1&page={word}'
        )
        if response.status_code != 200:
            raise WordNotFoundError(f"HTTP error {response.status_code} when looking up word '{word}'")

        data = response.json()
        if 'error' in data:
            raise WordNotFoundError(f"Word '{word}' not found in Wiktionary")

        # Store translations
        self.translations = data['parse'].get('langlinks')
        if self.translations is None:
            raise WordNotFoundError(f"No translations found for word '{word}'")

        # Get Dutch content
        self.xml_doc = ET.fromstring(data['parse']['text'])

    def try_get_sound_file_url(self):
        """Extract sound file URL from the Uitspraak section"""
        for elem in self.xml_doc:
            for a in elem.findall(".//a[@class='internal']"):
                if a.get('href', '').startswith('//upload.wikimedia.org') and a.get('title', '').endswith('.ogg'):
                    return "https:" + a.get('href')
        return None

    def try_get_image_url(self):
        """Extract the first content image URL"""
        for elem in self.xml_doc:
            # First try images in thumbinner (images with captions)
            for figure in elem.findall(".//div[@class='thumbinner']"):
                img = figure.find(".//img[@class='mw-file-element']")
                if img is not None and 'src' in img.attrib:
                    # Ignore small icons
                    width = int(img.get('width', '0'))
                    if width < 50:
                        continue
                    src = img.get('src')
                    if src.startswith('//upload.wikimedia.org'):
                        return "https:" + src

            # Then try regular content images
            for img in elem.findall(".//img[@class='mw-file-element']"):
                if 'src' in img.attrib:
                    # Ignore small icons and system images
                    width = int(img.get('width', '0'))
                    if width < 50:
                        continue
                    src = img.get('src')
                    if (
                        src.startswith('//upload.wikimedia.org') and
                        not src.endswith(('Icon.svg.png', 'Symbol.svg.png'))
                    ):
                        return "https:" + src
        return None

    def try_get_transcription(self):
        """Extract IPA transcription"""
        for elem in self.xml_doc:
            for span in elem.findall(".//span[@class='IPAtekst']"):
                return span.text
        return None

    def try_get_article(self):
        """Determine if it's 'de' or 'het' based on genus markers"""
        # Find Zelfstandig naamwoord header and get next paragraph
        zn_found = False
        for elem in self.xml_doc:
            # Mark when we find the Zelfstandig_naamwoord header within its div container
            if (elem.tag == 'div' and
                    elem.get('class') == 'mw-heading mw-heading4' and
                    elem.find('h4[@id="Zelfstandig_naamwoord"]') is not None):
                zn_found = True
                continue
            # Get the first paragraph after the header
            if zn_found and elem.tag == 'p':
                # Get all genus markers from spans inside links
                genus_markers = []
                for a in elem.findall(".//a[@title='WikiWoordenboek:Genus']"):
                    span = a.find(".//span")
                    if span is not None and span.text:
                        marker = span.text.strip()
                        if marker in ['m', 'v', 'o', 'g']:
                            genus_markers.append(marker)

                # Convert markers to article
                if 'o' in genus_markers:
                    if any(m in ['m', 'v', 'g'] for m in genus_markers):
                        return "de/het"
                    return "het"
                if any(m in ['m', 'v', 'g'] for m in genus_markers):
                    return "de"
                break

        return None

    def try_get_part_of_speech(self):
        """Get the part of speech (woordsoort) from the header"""
        # Look for heading divs containing part of speech headers
        for elem in self.xml_doc:
            if elem.tag == 'div' and elem.get('class') == 'mw-heading mw-heading4':
                h4 = elem.find('h4')
                if h4 is not None:
                    # Common parts of speech to check for
                    pos_set = {
                        'Zelfstandig_naamwoord',
                        'Werkwoord',
                        'Bijvoeglijk_naamwoord',
                        'Bijwoord',
                        'Tussenwerpsel',
                        'Voornaamwoord',
                        'Voorzetsel'
                    }

                    # Check if header id matches any part of speech
                    pos_id = h4.get('id')
                    if pos_id in pos_set:
                        return ' '.join(pos_id.lower().split('_'))

        return None

    def try_get_plural_form(self):
        """Get plural form from the infobox table"""
        # Find the infobox table first
        for table in self.xml_doc.findall(".//table[@class='infobox']"):
            # Look for the row containing meervoud in header
            for tr in table.findall(".//tr"):
                headers = tr.findall("th")
                if not headers:
                    continue

                # Check if this row contains the meervoud column
                meervoud_col = -1
                for i, th in enumerate(headers):
                    if th.find(".//a[@title='meervoud']") is not None:
                        meervoud_col = i
                        break

                if meervoud_col >= 0:
                    # Found the header row, now look for naamwoord row
                    for row in table.findall(".//tr"):
                        td = row.find("td[@class='infoboxrijhoofding']")
                        if td is not None and 'naamwoord' in ''.join(td.itertext()).lower():
                            # Get the meervoud cell
                            cells = row.findall("td")
                            if len(cells) > meervoud_col:
                                return ''.join(cells[meervoud_col].itertext()).strip()

        return None

    def try_download_sound(self):
        """Download the sound file and return the path"""
        sound_url = self.try_get_sound_file_url()
        if sound_url:
            extension = sound_url.rsplit('.', 1)[-1]
            sound_file_path = self.working_dir / self.word / f'{self.word}.{extension}'
            sound_file_path.parent.mkdir(parents=True, exist_ok=True)
            response = self.session.get(sound_url)
            if response.status_code != 200:
                raise WordNotFoundError(
                    f"HTTP error {response.status_code} when downloading sound file from '{sound_url}'"
                )
            with sound_file_path.open('wb') as f:
                f.write(response.content)
            return sound_file_path
        return None

    def try_download_image(self):
        """Download the image file and return the path"""
        image_url = self.try_get_image_url()
        if image_url:
            extension = image_url.rsplit('.', 1)[-1]
            image_file_path = self.working_dir / self.word / f'{self.word}.{extension}'
            image_file_path.parent.mkdir(parents=True, exist_ok=True)
            response = self.session.get(image_url)
            if response.status_code != 200:
                raise WordNotFoundError(
                    f"HTTP error {response.status_code} when downloading image file from '{image_url}'"
                )
            with image_file_path.open('wb') as f:
                f.write(response.content)
            return image_file_path
        return None
