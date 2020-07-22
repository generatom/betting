#!/usr/bin/env python3
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup


class Tips():
    def __init__(self, start_date, end_date=None):
        self.base_url = 'https://tipsbet.co.uk/free-betting-tips-'
        self.pickle_path = '/home/jono/projects/betting/df.pkl'
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.date.today()
        self.df = self._init_df()
        self.store_df()

    def _init_df(self, path=None):
        if path:
            df = pd.read_pickle(path)
        else:
            df = self._get_web_data()

        return df

    def _get_web_data(self):
        try:
            df = pd.DataFrame()
            current_date = self.start_date
            web_data = Webpage(self.base_url, current_date)

            while web_data.tip_df is not None and (
                    current_date < self.end_date):
                df = df.append(web_data.tip_df, ignore_index=True)
                current_date += datetime.timedelta(days=1)
                web_data = Webpage(self.base_url, current_date)
        except KeyboardInterrupt:
            print(df)
        finally:
            return df

    def store_df(self, path=None):
        if not path:
            path = self.pickle_path
        self.df.to_pickle(path)


class Webpage():
    def __init__(self, base_url, tip_date):
        self.url = base_url + tip_date.strftime('%d-%m-%Y')
        self.tip_date = tip_date
        self.tip_df = self.get_dataframe(self.url)
        self.tip_df.insert(0, 'Date', tip_date)

    def get_dataframe(self, url):
        page = requests.get(self.url)
        try:
            soup = self._interpret_html(page.text)
            df = pd.read_html(soup, header=0)[0]
            df.drop(columns=['Flag'], inplace=True)
            df[['Results', 'Status']] = df.Results.str.split('|', expand=True)
            return df
        except ValueError as e:
            print(url + ': ' + str(e))
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
    start_date = datetime.date(2020, 7, 21)
    s = Tips(start_date)
