from pathlib import Path
import requests
from bs4 import BeautifulSoup


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
        self.soup = BeautifulSoup(data['parse']['text'], 'html.parser')

    def try_get_sound_file_url(self):
        """Extract sound file URL from the Uitspraak section"""
        for a in self.soup.find_all("a", class_="internal"):
            href = a.get('href', '')
            title = a.get('title', '')
            if href.startswith('//upload.wikimedia.org') and title.endswith('.ogg'):
                return "https:" + href
        return None

    def try_get_image_url(self):
        """Extract the first content image URL"""
        # First try images in thumbinner (images with captions)
        for figure in self.soup.find_all("div", class_="thumbinner"):
            img = figure.find("img", class_="mw-file-element")
            if img and img.has_attr('src'):
                width = int(img.get('width', '0'))
                if width < 50:
                    continue
                src = img['src']
                if src.startswith('//upload.wikimedia.org'):
                    return "https:" + src

        # Then try regular content images
        for img in self.soup.find_all("img", class_="mw-file-element"):
            if img.has_attr('src'):
                width = int(img.get('width', '0'))
                if width < 50:
                    continue
                src = img['src']
                if (
                    src.startswith('//upload.wikimedia.org') and
                    not src.endswith(('Icon.svg.png', 'Symbol.svg.png'))
                ):
                    return "https:" + src
        return None

    def try_get_transcription(self):
        """Extract IPA transcription"""
        span = self.soup.find("span", class_="IPAtekst")
        if span:
            return span.get_text()
        return None

    def try_get_article(self):
        """Determine if it's 'de' or 'het' based on genus markers"""
        # Find Zelfstandig naamwoord header and get next paragraph
        zn_header = self.soup.find("h4", id="Zelfstandig_naamwoord")
        if zn_header:
            # Find the next paragraph after the header
            p = zn_header.find_next("p")
            if p:
                genus_markers = []
                for a in p.find_all("a", title="WikiWoordenboek:Genus"):
                    span = a.find("span")
                    if span and span.get_text():
                        marker = span.get_text().strip()
                        if marker in ['m', 'v', 'o', 'g']:
                            genus_markers.append(marker)
                if 'o' in genus_markers:
                    if any(m in ['m', 'v', 'g'] for m in genus_markers):
                        return "de/het"
                    return "het"
                if any(m in ['m', 'v', 'g'] for m in genus_markers):
                    return "de"
        return None

    def try_get_part_of_speech(self):
        """Get the part of speech (woordsoort) from the header"""
        pos_set = {
            'Zelfstandig_naamwoord',
            'Werkwoord',
            'Bijvoeglijk_naamwoord',
            'Bijwoord',
            'Tussenwerpsel',
            'Voornaamwoord',
            'Voorzetsel'
        }
        for h4 in self.soup.find_all("h4"):
            pos_id = h4.get('id')
            if pos_id in pos_set:
                return ' '.join(pos_id.lower().split('_'))
        return None

    def try_get_plural_form(self):
        """Get plural form from the infobox table"""
        for table in self.soup.find_all("table", class_="infobox"):
            # Find the header row with 'meervoud'
            header_row = None
            for tr in table.find_all("tr"):
                headers = tr.find_all("th")
                for i, th in enumerate(headers):
                    a = th.find("a", title="meervoud")
                    if a:
                        header_row = tr
                        meervoud_col = i
                        break
                if header_row:
                    break
            if header_row:
                # Find the row with 'naamwoord'
                for row in table.find_all("tr"):
                    td = row.find("td", class_="infoboxrijhoofding")
                    if td and 'naamwoord' in td.get_text().lower():
                        cells = row.find_all("td")
                        if len(cells) > meervoud_col:
                            return cells[meervoud_col].get_text(strip=True)
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
