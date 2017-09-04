#!/usr/bin/python3

import bs4
import collections
import multiprocessing
import requests

class CurrencyConverter:
    def __init__(self, base='EUR'):
        self.base = base
        self.rates = requests.get('http://api.fixer.io/latest').json()['rates']

    def __call__(self, currency, amount):
        return amount / self.rates[currency] 


class Comparator():
    def __init__(self, *sources):
        converter = CurrencyConverter()
        self.results = collections.defaultdict(lambda: [])
        
        for s in sources:
            for (tld, price, currency) in s:
                self.results[tld].append( (converter(currency, price), currency, price, type(s).__name__) )

        
        for prices in self.results.values():
            prices.sort()

    def __iter__(self):
        return self.results.items()

    def __item__(self, *a, **k):
        return self.results.__item__(*a,**k)
        

class Page:
    method = requests.get

    def __init__(self):
        r = type(self).method(type(self).url)
        r.raise_for_status()
        self._text = r.text
        self.data = list(self.extract(bs4.BeautifulSoup(r.text, 'html5lib')))

    def __iter__(self):
        return iter(self.data)



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
