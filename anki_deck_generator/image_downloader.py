import logging
import time
from pathlib import Path
from icrawler.builtin import GoogleImageCrawler


class ImageDownloader:
    def __init__(self, working_dir):
        self.working_dir = Path(working_dir)
        self.crawler = GoogleImageCrawler(storage={'root_dir': str(working_dir)}, log_level=logging.ERROR)

    def download_image(self, word):
        for _ in range(5):
            try:
                self.crawler.crawl(keyword=word, max_num=1, overwrite=True)
                break
            except Exception:
                time.sleep(1)
                continue
        else:
            logging.error(f"Cannot find an image for the word '{word}'")
            return None
        image_file = next(self.working_dir.glob('000001.*'))
        new_name = self.working_dir / word / f'{word}{image_file.suffix}'
        image_file.rename(new_name)
        return new_name
