#!/usr/bin/env python3
import shelve
import requests
from datetime import date
import pandas as pd
from bs4 import BeautifulSoup


class Tips():
    def __init__(self, start_date):
        pass


class Webpage():
    def __init__(self, base_url, tip_date, tips_data):
        self.url = base_url + tip_date.strftime('%d-%m-%Y')
        self.tip_date = tip_date
        self.tip_df = self.get_dataframe(self.url)
        print(self.tip_df)

    def get_dataframe(self, url):
        page = requests.get(self.url)
        try:
            soup = self._interpret_html(page.text)
            df = pd.read_html(soup, header=0)[0]
            df.drop(columns=['Flag'], inplace=True)
            df[['Results', 'Status']] = df.Results.str.split('|', expand=True)
            return df
        except ValueError as e:
            print(e)
            return None

    def _interpret_html(self, html):
        gif_base = 'https://tipsbet.co.uk/wp-content/uploads/2017/01/'
        sport = {gif_base + 'fotbal.gif': 'Football',
                 gif_base + 'tenis.gif': 'Tennis',
                 gif_base + 'tenis-1.gif': 'Tennis',
                 gif_base + 'tennis_ball.gif': 'Tennis',
                 gif_base + 'basket.gif': 'Basketball'
                 }
        stats = {'color: #008000;': 'W', 'color: #ff0000;': 'L'}
        soup = BeautifulSoup(html, 'lxml')
        images = soup.select('span img')
        results = soup.select('table#table-tipsbet td')[17::9]

        for img in images:
            parent = img.parent
            if img['src'] in sport:
                current_sport = sport[img['src']]
            else:
                current_sport = 'Unknown'
            img.decompose()
            parent.string = current_sport

        for res in results:
            s = [score for score in res.strings][0]
            s_res = s + ' | '
            s_res += stats[res.select('span')[-1]['style']] if s != '?' else s
            s.replace_with(s_res)

        return bytes(soup.encode())


if __name__ == '__main__':
    base_url = 'https://tipsbet.co.uk/free-betting-tips-'
    start_date = date(2020, 7, 21) # date.today()
    tips_data = Tips(start_date)
    s = Webpage(base_url, start_date, tips_data)
