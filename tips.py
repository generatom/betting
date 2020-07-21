#!/usr/bin/env python3
from bs4 import BeautifulSoup
import shelve
import requests
from datetime import date
import pandas as pd


class Tips():
    def __init__(self, date):
        pass


class Webpage():
    def __init__(self, base_url, tip_date):
        self.url = base_url + tip_date.strftime('%d-%m-%y')
        self.tip_date = tip_date
        # self.soup = BeautifulSoup(self.get_page(self.url), 'lxml')
        # self.tip_table = self.soup.find('table', {'id': 'table-tipsbet'})
        self.tip_df = pd.read_html(self.get_page(self.url))
        print(self.tip_df)

    def get_page(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.content


if __name__ == '__main__':
    base_url = 'https://tipsbet.co.uk/free-betting-tips-'
    start_date = date.today()
    s = Webpage(base_url, start_date)
