#!/usr/bin/env python3
import requests
import datetime as dt
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from bs4 import BeautifulSoup


class Tips():
    def __init__(self, start_date=None, end_date=None, verbosity=0):
        self.verbosity = verbosity
        self.base_url = 'https://tipsbet.co.uk/free-betting-tips-'
        self.pickle_path = '/home/jono/projects/betting/df.pkl'
        self.start_date = start_date if start_date else dt.datetime.now()
        self.end_date = end_date if end_date else dt.datetime.now()
        self.df = pd.DataFrame()
        self.init_df()
        self.store_df()

    def init_df(self):
        if self._check_pickle():
            if self.verbosity:
                print('Pickle checked and loaded.')
        else:
            if self.verbosity:
                print('Getting data from web...')
            self.df = self._get_web_data()
            self.full_dataset = self.df.copy()

    def _check_pickle(self, path=None, sdate=None, edate=None):
        if path is None:
            path = self.pickle_path
        if sdate is None:
            sdate = self.start_date
        if edate is None:
            edate = self.end_date

        try:
            self.full_dataset = pd.read_pickle(path)
        except OSError:
            return False

        df = self.full_dataset

        # If no pickle data, get from web
        if df.empty:
            print('No data in pickle')
            return False

        # If start_date already in pickle, restrict df to dates greater than
        # start_date. Otherwise, get from web
        if sdate.date() in df.Time.dt.date.values:
            if self.verbosity:
                print(f'Restricting dates to date >= {sdate.date()}')
            self.df = df[df.Time >= sdate].copy()
        else:
            end_date = df.Time.min() - dt.timedelta(days=1)
            if self.verbosity:
                print(f'Getting data for {sdate.date()} - {end_date.date()}')
            new_data = self._get_web_data(sdate, end_date)
            self.df = self.df.append(new_data, ignore_index=True)

        # If end_date already in pickle, restrict df to dates less than edate.
        # Else get from web
        if edate.date() in df.Time.dt.date.values:
            if self.verbosity:
                print(f'Restricting dates to date < {edate.date()}')
            self.df = self.df.append(df[df.Time < edate +
                                     dt.timedelta(days=1)]).drop_duplicates()
        else:
            start_date = df.Time.max() + dt.timedelta(days=1)
            if self.verbosity:
                print(f'Getting data for {start_date.date()} - {edate.date()}')
            new_data = self._get_web_data(start_date, edate)
            self.df = self.df.append(new_data, ignore_index=True)

        self.full_dataset = self.full_dataset.append(self.df,
                                                     ignore_index=False)
        self.full_dataset.drop_duplicates(ignore_index=True, inplace=True)

        return True

    def _get_web_data(self, sdate=None, edate=None):
        if sdate is None:
            sdate = self.start_date
        if edate is None:
            edate = self.end_date
        if edate.date() > dt.date.today():
            edate = dt.datetime.now()

        try:
            df = pd.DataFrame()
            current_date = sdate
            web_data = Webpage(self.base_url, current_date)

            while current_date.date() <= edate.date():
                if web_data.tip_df is not None:
                    if self.verbosity > 1:
                        print(f'Adding {current_date.date()}')
                    df = df.append(web_data.tip_df, ignore_index=True)
                else:
                    if self.verbosity > 1:
                        print(f'No tips for {current_date.date()}')

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
        self.full_dataset.to_pickle(path)

    def plot_status(self, by='Sport', relative=True, labels=True):
        summary = self.df[[by, 'Status']]
        order = ['W', 'L', '?']

        sm = summary.groupby([by, 'Status'], as_index=False).size()
        sm = sm.unstack().fillna(0)
        if relative:
            sm['Total'] = sm.sum(axis=1)
            sm = sm.drop('Total', axis=1).div(sm.Total, axis=0) * 100
            f_string = '{:.2f}%'
        else:
            f_string = '{:.0f}'

        strip = np.vectorize(str.strip)
        sm.columns = pd.CategoricalIndex(strip(sm.columns.values),
                                         ordered=True)
        sm.columns = sm.columns.reorder_categories(new_categories=order)
        sm = sm.sort_index(axis=1)
        # sm['Total'] = sm['W'] + sm['L'] + sm['?']

        ax = sm.plot(kind='bar', stacked=True, figsize=(14, 10))

        if labels:
            for p in ax.patches:
                width, height = p.get_width(), p.get_height()
                x, y = p.get_xy()
                ax.text(x + width / 2.0, y + height / 2.0,
                        f_string.format(height), horizontalalignment='center',
                        verticalalignment='center')

        plt.show()


class Webpage():
    def __init__(self, base_url, tip_date):
        self.url = base_url + tip_date.strftime('%d-%m-%Y')
        self.tip_date = tip_date
        self.tip_df = self.get_dataframe(self.url)
        if self.tip_df is not None:
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
        except ValueError:
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
    start_date = dt.datetime(2020, 4, 10)
    end_date = start_date + dt.timedelta(days=10)
    s = Tips(start_date, end_date)
    print(f'Restricted:\n{s.df}\nMin: {s.df.Time.min()}\nMax: ' +
          f'{s.df.Time.max()}')
    print(f'Full:\n{s.full_dataset}\nMin: {s.full_dataset.Time.min()}\nMax: ' +
          f'{s.full_dataset.Time.max()}')
