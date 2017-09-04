#!/usr/bin/python3

import requests
import bs4

class Page:
    method = requests.get

    def fetch(self):
        r = type(self).method(type(self).url)
        r.raise_for_status()
        return bs4.BeautifulSoup(r.text, 'html5lib')

    def __iter__(self):
        yield from self.extract(self.fetch())

class Infomaniak(Page):
    method = requests.post
    url = 'https://www.infomaniak.com/fr/domaines/tarifs/toutes'

    def extract(self, html):
        tab = (html.find(name='table', id='result_domains') 
                   .find(name='tbody'))
        for row in tab.find_all('tr', class_='results prices'):
            cells = row.find_all('td')
            tld = cells[1].text.strip()
            price = float(
                (cells[2].find('span', class_='promo-alt') or
                 cells[2].find('span')).text.strip())
            yield (tld, price, 'CHF')
        

class Dynadot(Page):
    url = 'https://www.dynadot.com/domain/tlds.html?price_level=0'

    def extract(self, html):
        tab = html.find(name='div', id='St_Data_Info')
        for row in tab.find_all('p', class_='tld-content'):
            tld = row.find('a').text
            price = float(row.find('span', class_='span-register-price').text.strip()[1:])
            yield (tld, price, 'USD')

class Gandi(Page):
    url = 'https://v4.gandi.net/domaine/prix/info'

    def extract(self, html):
        for tab in html.findAll('table', class_='gtable'):
            for row in tab.find_all('tr'):
                if 'id' in row:
                    tld = '.' + row['id']
                    price = float(row.findAll('td')[1].find('div').text.strip().split()[0].replace(',','.'))
                    yield (tld, price, 'EUR')


def main():
    print(list(Gandi()))

if __name__ == '__main__':
    main()
