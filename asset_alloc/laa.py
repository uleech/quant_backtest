import FinanceDataReader as fdr
import datetime
import pandas as pd
import queue
import threading
import quantstats as qs
import statistics as st
from dateutil.relativedelta import relativedelta

# 공격 자산군
RISK_IDX = 0
BOND_IDX = 1
CANARY_IDX = 2

assets = ['IWD', 'GLD', 'IEF', 'SHY', 'QQQ', 'SPY']

start_date = '1999-01-01'
# 실제 시작 보다 1년전을 지정
end_date = '2021-12-31'

transactions = []
returns = []
cnt = 0

class transaction:
    def __init__(self, name, buy_date, sell_date, buy_price, sell_price):
        self._name = name
        self._buy_date = buy_date
        self._sell_date = sell_date
        self._buy_price = buy_price
        self._sell_price = sell_price
        self._return = sell_price - buy_price
        self._return_pct = self._return / self._buy_price

    def __str__(self):
        return '%s: buy(%s), sell(%s), pct(%f)' % (self._name, self._buy_date, self._sell_date, self._return_pct)

def get_un_rate():
    data = pd.read_excel('UNRATE.xls')
    data.rename(columns={'FRED Graph Observations': 'Date', 'Unnamed: 1': 'Rate'}, inplace=True)
    data = data[10:]
    data.set_index('Date', inplace=True)
    data['Rate'] = pd.to_numeric(data['Rate'], downcast='float')
    mom = data.rolling(window=12).mean()
    return data, mom

def get_data(start_date, end_date):
    assets_df = []

    def fetch_data(name, start_date, end_date):
        v = None
        try:
            v = fdr.DataReader(name, start_date, end_date).resample('M').last()
            v.rename(columns={'Close': name}, inplace=True)
            v.drop(['Open', 'High', 'Low', 'Volume', 'Change'], axis=1, inplace=True)
        except Exception as e:
            print(e)
        finally:
            return assets_df.append(v)

    data_queue = queue.Queue()
    for n in assets:
        t_id = threading.Thread(target=fetch_data, args=(n, start_date, end_date))
        data_queue.put(t_id)
        t_id.start()

    while not data_queue.empty():
        t_id = data_queue.get()
        if t_id.is_alive():
            t_id.join()

    assets_df_merged = pd.concat(assets_df, axis=1, join='inner')
    return assets_df_merged

def select()
    try:
        '''
           result = assets_prices[BOND_IDX].loc[index].idxmax()
            transactions.append([transaction(result, buy_date, sell_date,
                             assets_prices[RISK_IDX].loc[buy_date][result],
                             assets_prices[RISK_IDX].loc[sell_date][result])]) '''
    except Exception as e:
        print(e)

all_assets_price = get_data(start_date, end_date)
un_rate, mom_un_rate = get_un_rate()
spy_mom = fdr.DataReader('SPY').rolling(window=200).mean()
spy_mom = spy_mom.resample('M').last()

for idx in range(1, len(all_assets_price)):
    try:
        buy_date = all_assets_price.index[idx - 1]
        sell_date = all_assets_price.index[idx]
        un_rate_date = buy_date
        un_rate_date = un_rate_date - datetime.timedelta(months=1)
        un_rate_date = un_rate_date.replace(days=1)

        alloc_assets = ['IWD', 'GLD', 'IEF']

        if un_rate[un_rate_date]['Rate'] > mom_un_rate[un_rate_date]['Rate'] and spy_mom.index[buy_date]['Close'] > alloc_assets['SPY']:
            alloc_assets.append('SHY')
        else:
            alloc_assets.append('QQQ')

        transactions.append(list(map(lambda x : transaction(x, buy_date, end_date,
                                all_assets_price.iloc[idx - 1][x],
                                all_assets_price.iloc[idx][x]), alloc_assets)))
    except Exception as e:
        print(e)

report = []

for x in transactions:
    item = {}
    v = 0
    for i in x:
        v = v + i._return_pct
    pct = v / len(x)
    item['Date'] = pd.to_datetime(x[0]._sell_date)
    item['Earn'] = pct
    report.append(item)

out_df = pd.DataFrame.from_dict(report).dropna(axis=0)
out_df.set_index('Date', inplace=True)
out_df.sort_index(axis=1, ascending=True)
qs.reports.html(out_df['Earn'], 'SPY', output='.report.html')

for x in transactions:
    for y in x:
        print('%s: buy(%s), sell(%s), pct(%f)' % (y._name, y._buy_date, y._sell_date, y._return_pct))

#map(lambda x: print(x), transactions)

# risk_price = pd.DataFrame.from_dict(t);
# risk_price = risk_price.set_index('Date')
# risk_momentum = pd.DataFrame.from_dict(t);
# risk_momentum = risk_momentum.set_index('Date')
# bond_price = pd.DataFrame.from_dict(t);
# bond_price = bond_price.set_index('Date')
# bond_momentum
# 다 가져 와서, 긴 것 위무로 만들고 나머지 다 0

# 자산군의 데이터 획득
# 자산군의 모멘텀 스코어 계산
# 12 * 최근 1개월 수익 + 4 * 최근 3개월 수익 + 2 * 최근 6개월 수익 + 1 * 최근 12개월 수익
# 20, 60, 120, 240
# simulation 수행
# simul 의 편의를 위해 매달 다팔고, 다 사는 것으로 수행
# 거래 비용은 계산 하지 않음 (NH 농협 기준, 거래세 없음, 유관 비용 수수료 가 미비 하게 존재)
# 세금은 55세 일시 수령 5.5%로 계산

# trade { n, b, s, r}
# sel [n1, n2]
