import FinanceDataReader as fdr
import datetime
import pandas as pd
import queue
import threading
import quantstats as qs

# 공격 자산군
RISK_IDX = 0
BOND_IDX = 1
CANARY_IDX = 2

risk_asset = ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'VWO', 'VNQ', 'GSG', 'GLD', 'TLT', 'HYG', 'LQD']
# 수비 자산군
bond_asset = ['SHY', 'IEF', 'LQD']
# 위험 탐지 자산군
canary_asset = ['BND', 'VWO']
assets = [risk_asset, bond_asset, canary_asset]
start_date = '1999-01-01'
# 실제 시작 보다 1년전을 지정
end_date = '2021-12-31'

assets_prices = []
assets_momentum = []

date_list = fdr.DataReader('SPY', start_date, end_date).resample('M').last().index.tolist()
init_list = [0 for idx in range(len(date_list))]

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


def get_data(asset_idx):
    v_list = []
    mom_list = []

    def cal_momentum(x):
        print(x)
        return_v = (x[-1] - x[-2]) * 12 + 4 * (x[-1] - x[-4]) + 2 * (x[-1] - x[-7]) + x[0]
        return return_v

    def fetch_data(idx):
        def update_data(dest_data, dest_idx, data):
            for id, row in data.iterrows():
                dest_data[dest_idx].loc[str(id.date())][idx] = row[idx]
        try:
            v = fdr.DataReader(idx, start_date, end_date).resample('M').last()
            v.drop(['Open', 'High', 'Low', 'Volume', 'Change'], axis=1, inplace=True)
            v.columns = [idx]
            update_data(assets_prices, asset_idx, v)
            mom = v.rolling(window=12).apply(lambda x: cal_momentum(x))
            update_data(assets_momentum, asset_idx, mom)
        except Exception as e:
            print(e)

    data_queue = queue.Queue()
    for asset_name in assets[asset_idx]:
        #fetch_data(asset_name)
        t_id = threading.Thread(target=fetch_data, args=(asset_name,))
        data_queue.put(t_id)
        t_id.start()

    while not data_queue.empty():
        t_id = data_queue.get()
        if t_id.is_alive():
            t_id.join()

    print(assets_momentum)
    print(assets_prices)

def pick_last():
    try:
        index = canary_momentum.index.tolist()[-1]
        bnd = canary_momentum.loc[index]['BND']
        vwo = canary_momentum.loc[index]['VWO']
        result = []

        if bnd > 0 and vwo > 0:
            result = assets_prices[RISK_IDX].loc[index].nlargest(2)
        elif bnd > 0 or vwo > 0:
            result1 = assets_prices[RISK_IDX].loc[index].idxmax()
            result2 = assets_prices[BOND_IDX].loc[index].idxmax()
            result.append(result1, result2)
        else:
            result.append(assets_prices[BOND_IDX].loc[index].idxmax())
    except Exception as e:
        print(e)
    finally:
        return result

def select(idx, canary_momentum):
    # [Date, BND, VWO]
    # 위험 자산 투자
    try:
        index = str(idx.date())
        n_index = assets_prices[RISK_IDX].index.get_loc(index)
        buy_date = index
        sell_date = str(assets_prices[RISK_IDX].index[n_index + 1].date())
        if n_index + 1 == len(assets_prices):
            return

        bnd = canary_momentum.loc[index]['BND']
        vwo = canary_momentum.loc[index]['VWO']
        if bnd == 0 and vwo == 0:
            return

        if bnd > 0 and vwo > 0:
            # 해당일에 리스크 자산중 큰 두개 구하기
            result = assets_prices[RISK_IDX].loc[index].nlargest(2)
            t = []
            for r in range(2):
                t.append(transaction(result.index[r], buy_date, sell_date,
                         assets_prices[RISK_IDX].loc[buy_date][r],
                         assets_prices[RISK_IDX].loc[sell_date][r]))
            transactions.append(t)
        elif bnd > 0 or vwo > 0:
            result1 = assets_prices[RISK_IDX].loc[index].idxmax()
            result2 = assets_prices[BOND_IDX].loc[index].idxmax()
            transactions.append(
                [transaction(result1, buy_date, sell_date,
                             assets_prices[RISK_IDX].loc[index][result1],
                             assets_prices[RISK_IDX].loc[sell_date][result1],
                             ),
                 transaction(result2, buy_date, sell_date,
                             assets_prices[RISK_IDX].loc[index][result2],
                             assets_prices[BOND_IDX].loc[index][result2])])
        else:
            result = assets_prices[BOND_IDX].loc[index].idxmax()
            transactions.append([transaction(result, buy_date, sell_date,
                             assets_prices[RISK_IDX].loc[buy_date][result],
                             assets_prices[RISK_IDX].loc[sell_date][result])])
    except Exception as e:
        print(e)

for asset in assets:
    t = {}
    for idx in asset:
        t[idx] = init_list
    t['Date'] = date_list
    assets_prices.append(pd.DataFrame.from_dict(t).set_index('Date'))
    assets_momentum.append(pd.DataFrame.from_dict(t).set_index('Date'))
    get_data(cnt)
    cnt = cnt + 1

for idx, canary_momentum in assets_momentum[CANARY_IDX].iterrows():
    select(idx, assets_momentum[CANARY_IDX])


report = []

for x in transactions:
    pct = 0
    item = {}
    if len(x) > 1:
        pct = (x[0]._return_pct + x[1]._return_pct) / 2
    else:
        pct = x[0]._return_pct
    item['Date'] = pd.to_datetime(x[0]._sell_date)
    item['Earn'] = pct
    report.append(item)

out_df = pd.DataFrame.from_dict(report).dropna(axis=0)
out_df.set_index('Date', inplace=True)
out_df.sort_index(axis=1, ascending=True)
qs.reports.html(out_df['Earn'], 'SPY', output='.report.html')



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
