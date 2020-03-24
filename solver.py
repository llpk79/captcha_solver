import urllib3
import tqdm
from bs4 import BeautifulSoup as bsoup


class ZipRecruiterScraper(object):
    def __init__(self, pages: int, num_jobs: int, city: str, state: str, terms: str) -> None:
        self.pages = pages
        self.num_jobs = num_jobs
        self.city = city
        self.state = state
        self.terms = terms
        self.url = self.build_url()
        self.http = urllib3.PoolManager()
        self.descriptions = None

    def build_url(self) -> str:
        """Builds search url from user input."""
        url = 'www.ziprecruiter.com/candidate/search?radius=25&search=' \
              f"{'+'.join(self.terms.split())}&location={'+'.join(self.city.split())}%2C+{self.state}"
        print(f'\nZipRecruiter search URL: {url}')
        return url

    @staticmethod
    def find_long_descriptions(soup) -> list:
        """Get a list of urls to long form job descriptions."""
        urls = []
        # for div in soup.find_all(name='div',
        #                          attrs={'class': 'job_content'}):
        for a in soup.find_all(name='a',
                               attrs={'class': 'job_link t_job_link'}):
            print(a)
            urls.append(a['href'])
        return urls

    def get_next_pages(self) -> list:
        """Create a list of top level pages to search."""
        return [self.url + f'&page={x}' for x in range(self.pages)]

    def get_catchpa_form(self, soup) -> str:
        """Get captcha form data."""
        iframe = soup.find(name='iframe')
        src = iframe['src']
        image = self.http.request('GET',
                                  src)
        # print('image ', image.data)
        return image.data

    @staticmethod
    def get_captcha_target(soup):
        div = soup.find(name='div',
                        attrs={'class': 'rc-imageselect-desc-no-canonical'})
        # print('div ', div.text.split('with')[1])
        if not div:
            div = soup.find(name='div',
                            attrs={'class': 'rc-imageselect-desc'})
        return div.text.split('with')[1]

    def get_captcha_image(self, soup):
        """Retrieve captcha image for solving."""
        div = soup.find(name='img',
                        attrs={'class': 'fbc-imageselect-payload'})
        src = div['src']
        image_bytes_noise = str(self.http.request('GET',
                                              'www.google.com' + src).data)
        valid = [*list(range(10)), 'a', 'b', 'c', 'd', 'e', 'f']
        image_bytes_noiseless = [samp[:2] for samp in image_bytes_noise[1:].split('x')[1:]
                                 if samp[0] in valid and samp[1] in valid
                                 ]
        image_bytes = [bytearray.fromhex(samp) for samp in image_bytes_noiseless]
        image = [int.from_bytes(image_byte, byteorder='little') for image_byte in image_bytes]
        print(len(image))
        return image

    def get_descriptions(self) -> None:
        """Create a list of strings taken from long form job descriptions."""
        for page in tqdm(self.get_next_pages()):
            request = self.http.request('GET',
                                        page,
                                        headers={'User-Agent': 'opera'})
            base_soup = bsoup(request.data, 'html.parser')
            # print(base_soup)
            captcha_form = self.get_catchpa_form(base_soup)
            # print(captcha_form)
            captcha_soup = bsoup(captcha_form, 'html.parser')
            print(self.get_captcha_target(captcha_soup))
            print(self.get_captcha_image(captcha_soup))

        #     for url in self.find_long_descriptions(base_soup):
        #         if 'ziprecruiter' in url:
        #             request = self.http.request('GET',
        #                                         url,
        #                                         headers={'User-Agent': 'opera'},
        #                                         retries=urllib3.Retry(connect=500,
        #                                                               read=2,
        #                                                               redirect=50))
        #             soup = BeautifulSoup(request.data, 'html.parser')
        #             title = soup.find_all(name='h1',
        #                                   attrs={'class': 'job_title'})
        #             description = soup.find_all(name='div',
        #                                         attrs={'class': 'jobDescriptionSection'})
        #             if description:
        #                 self.descriptions.append((url, title.text, description.text))
        # return self.descriptions

