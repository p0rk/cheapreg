#!/usr/bin/python3

import bs4
import collections
import threading
import requests

class CurrencyConverter:
    """ Gets forex rates from fixer.io and converts currencies
    >>> c = CurrencyConverter('EUR')
    >>> c('USD', 10)
    8.3998
    
    (10 USD is 8.39 EUR)

    """
    def __init__(self, base='EUR'):
        self.base = base
        self.rates = requests.get('http://api.fixer.io/latest?base={}'.format(base)).json()['rates']

    def __call__(self, currency, amount):
        if currency == self.base:
            return amount
        return amount / self.rates[currency] 



class Comparator():
    """ Compares domain prices using conv

    >>> c = Comparator(OVH(), DynaDot())
    >>> c['.com']
    [(7.99, 'EUR', 7.99, 'OVH'), (8.3914, 'USD', 9,99, 'Dynadot')]

    Best price is 7.99 € at OVH, or 9.99$ at Dynadot (which converts to 8.391 EUR)

    """
    def __init__(self, *sources, currency='EUR'):
        converter = CurrencyConverter(base=currency)
        self.converter = converter
        self.results = collections.defaultdict(lambda: [])
        
        for s in sources:
            for (tld, price, currency) in s:
                self.results[tld].append( (converter(currency, price), currency, price, type(s).__name__) )

        
        for prices in self.results.values():
            prices.sort()

    def __iter__(self):
        return iter(self.results)

    def __getitem__(self, *a, **k):
        return self.results.__getitem__(*a,**k)

    def pretty(self):
        for tld in sorted(self):
            print("{}:".format(tld))
            for (price, currency, orig_price, supplier) in self[tld]:
                print("  {} {} from {} (original: {} {})".format(self.converter.base, price, supplier, currency, orig_price))

        

class Page:
    method = requests.get

    def __init__(self, skip=False):
        if not skip:
            self.fetch()

    def fetch(self):
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

class OVH(Page):
    url = 'https://www.ovh.com/fr/domaines/tarifs/'

    def extract(self, html):
        tab = html.find('table', id='dataTable')
        for row in tab.find_all('tr', class_='list-group-item'):
            tld = row['data-ext']
            price = float(row.find('td', attrs={'data-title': 'Création'})['data-order'])
            yield (tld, price, 'EUR')


class DomainContext(Page):
    url = 'http://www.domaincontext.com/pricing/'

    def extract(self, html):
        tab = html.find('div', id='DOMAIN').find('table')
        for row in tab.find_all('tr'):
            cells = row.find_all('td')
            if cells:
                tld = '.' + cells[0].text.strip()
                price = float(cells[1].text.strip().split()[0])
                yield (tld, price, 'USD')


all = [Infomaniak, Dynadot, Gandi, OVH, DomainContext]

def main():
    sources = [ s(skip=True) for s in all ]
    threads = [ threading.Thread(group=None, target=s.fetch) for s in sources ]
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    Comparator(*sources).pretty()

if __name__ == '__main__':
    main()
