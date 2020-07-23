#!/usr/bin/env python3
import requests
import datetime as dt
import pandas as pd
from bs4 import BeautifulSoup
from pprint import pprint


class Tips():
    def __init__(self, start_date=None, end_date=None):
        self.base_url = 'https://tipsbet.co.uk/free-betting-tips-'
        self.pickle_path = '/home/jono/projects/betting/df.pkl'
        self.start_date = start_date if start_date else dt.datetime.now()
        self.end_date = end_date if end_date else dt.datetime.now()
        self.df = pd.DataFrame()
        self.init_df()
        self.store_df()

    def init_df(self):
        if self._check_pickle():
            print('Pickle checked and loaded.')
        else:
            print('Getting data from web...')
            self.df = self._get_web_data()

    def _check_pickle(self, path=None, sdate=None, edate=None):
        if path is None:
            path = self.pickle_path
        if sdate is None:
            sdate = self.start_date
        if edate is None:
            edate = self.end_date

        try:
            df = pd.read_pickle(path)
        except OSError:
            return False

        self.full_dataset = pd.DataFrame(df)

        # If no pickle data, get from web
        if df.empty:
            print('No data in pickle')
            return False

        # If start_date already in pickle, restrict df to dates greater than
        # start_date. Otherwise, get from web
        if sdate.date() in df.Time.dt.date.values:
            print(f'Restricting dates to date > {sdate}')
            self.df = df[df.Time > sdate]
        else:
            print(f'{sdate.date()} not in:')
            pprint(df.Time.dt.date.values)
            end_date = df.Time.min()
            self.df.append(self._get_web_date(sdate, end_date),
                           ignore_index=True, sort=True)

        # If end_date already in pickle, restrict df to dates less than edate.
        # Else get from web
        if edate.date() in df.Time.dt.date.values:
            print(f'Restricting dates to date < {edate+dt.timedelta(days=1)}')
            self.df = self.df[self.df.Time < edate + dt.timedelta(days=1)]
        else:
            print('End date not in df, getting from web')
            return False

        return True

    def _get_web_data(self, sdate=None, edate=None):
        if sdate is None:
            sdate = self.start_date
        if edate is None:
            edate = self.end_date

        try:
            df = pd.DataFrame()
            current_date = sdate
            web_data = Webpage(self.base_url, current_date)

            while web_data.tip_df is not None and \
                    current_date.date() <= edate.date():
                df = df.append(web_data.tip_df, ignore_index=True)
                current_date += dt.timedelta(days=1)
                web_data = Webpage(self.base_url, current_date)
        except Exception as e:
            print(e)
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
        self.tip_df['Date'] = str(self.tip_date)
        self.tip_df['Time'] = pd.to_datetime(self.tip_df.Date + ' ' +
                                             self.tip_df.Time)
        self.tip_df.drop(columns=['Date'], inplace=True)

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
    start_date = dt.datetime(2020, 6, 22)
    s = Tips(start_date)
    print(s.df.Status.value_counts())
