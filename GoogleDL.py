
import requests
import os
import pathlib
import time
import selenium

from bs4 import BeautifulSoup
from tqdm import tqdm


class GoogleImage:
    """
    Google images downloader.

    When parameters is set up, there are available function and attributes:
        - `download()`
        - `close()`
        - `all_files`

    """
    def __init__(self, driver, time_sleep=1, verbose=True,
                 ext_default='.png', close_after_download=True, make_dir=True):
        """

        driver: selenium webdriver (Chrome, Firefox or Safari) used to web-scraping.
        time_sleep: time waiting in secondes for download each images (default: 1)
                    NOTE: If images are not downloaded, increase this parameter.
        verbose: bool, show progress bar (default: True).
        ext_default: str, when images has no extension, the default extension
                    will be added (default: '.png').
        close_after_download: bool, when download is done, close the webdriver
                            (default: True).
        make_dir: bool, (default: True) create a directory when download is launched.

        ---
        Use example:
        >>> from selenium import webdriver
        >>> driver = webdriver.Firefox()
        >>> google_dl = GoogleImage(driver=driver)
        >>> request = 'Cat'
        >>> google_dl.download(requete=request, n_images=10)

        """
        self.driver = driver
        self.time_sleep = time_sleep
        self.verbose = verbose
        self.all_files = []
        self.ext_default = ext_default
        self.close_after_download = close_after_download
        self.make_dir = make_dir

    def close(self):
        "Close the webdriver."
        self.driver.close()

    def download(self, request, n_images, directory=None, name=None):
        """
        Download images with the webdriver.

        Parameters:
        ----------
        request: str, request searched in google image.
        n_images: int, number of images downloaded.
        directory: str, where images are downloaded.
        name: str, name of the directory and files (default: None).
                If None, the name is given by the request.

        """
        url = f"https://www.google.fr/search?q={request}&tbm=isch&pws=0"
        n_downloads = 0
        n_unload = 0
        n_str = len(str(n_images))

        self.driver.get(url)
        self.name = name
        if self.name is None:
            self.name = request
        self.n_images = n_images

        self._scroll(driver=self.driver, time_sleep=self.time_sleep)
        all_img = self.driver.find_elements_by_class_name('isv-r')

        if self.verbose:
            all_img = tqdm(all_img[:n_images], desc=self.name, leave=True)

        for im in all_img:
            if self._verify_image(im):
                im.click()
            else:
                if self.verbose:
                    n_unload += 1
                    all_img.set_postfix({'unloaded': n_unload})
                continue
            img = self.driver.find_element_by_id('islsp')
            time.sleep(self.time_sleep)
            soup_img = BeautifulSoup(
                img.get_attribute('innerHTML'), 'lxml')
            balise_link = soup_img.select('img[src*="http"]')

            if len(balise_link) < 1:
                if self.verbose:
                    n_unload += 1
                    all_img.set_postfix({'unloaded': n_unload})
                continue

            link = balise_link[0]["src"]
            name_img = f'{self.name}_{n_downloads:0{n_str}d}'
            file = self._download_img(link, directory=directory,
                                        name=name_img,
                                        ext_default=self.ext_default,
                                        make_dir=self.make_dir)

            if file is not None:
                n_downloads += 1
                self.all_files.append(file)

            if self.verbose and file is None:
                n_unload += 1
                all_img.set_postfix({'unloaded': n_unload})

        if self.close_after_download:
            self.close()

    def _scroll(self, driver, time_sleep=1):
        last_height = driver.execute_script(
            "return document.body.scrollHeight")

        while True:
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(time_sleep)
            new_height = driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                actualise = driver.find_element_by_class_name('mye4qd')
                if actualise.size['height'] > 0 and actualise.size['width'] > 0:
                    actualise.click()
                else:
                    break
            last_height = new_height
            if len(driver.find_elements_by_class_name('isv-r')) > self.n_images:
                break

    def _download_img(self, link,
                      directory=None,
                      ext_default='.png',
                      name=None,
                      make_dir=True):
        if 'http' in link:
            _, ext = os.path.splitext(os.path.basename(link))
            self.VALID_EXTENTION = (".png", ".jpg", ".jpeg")
            if ext not in self.VALID_EXTENTION:
                ext = ext_default
            name += ext
            path = self._create_path_name(directory=directory,
                                        make_dir=make_dir)
            if path is not None:
                self._create_path(path)
                file = os.path.join(path, name)
            else:
                file = name
            try:
                with open(file, "wb") as f:
                    f.write(requests.get(link).content)
            except Exception:
                return None
            return file

    def _verify_image(self, element):
        source_element = element.get_attribute('innerHTML')
        balise = BeautifulSoup(source_element, 'lxml').find(
            class_="dPO1Qe gadasb")
        if balise is None:
            return True
        return None

    def _create_path(self, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    def _create_path_name(self, directory=None, make_dir=True):
        if directory is None:
            directory = ''
        if make_dir:
            path = os.path.join(directory, self.name)
            return path
        return None
