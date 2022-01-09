import FinanceDataReader as fdr
import datetime
import pandas as pd

# 공격 자산군
risk_asset = ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'VWO', 'VNQ', 'GSG', 'GLD', 'TLT', 'HYG', 'LQD']
# 수비 자산군
bond_asset = ['SHY', 'IEF', 'LQD']
# 위험 탐지 자산군
canary_asset = ['BND', 'VWO']

start_date = '1999-01-01'
# 실제 시작 보다 1년전을 지정
end_date = '2021-12-31'

max_dates = []
date_list = fdr.DataReader('SPY', start_date, end_date).resample('M').last().index.tolist()
init_list = [0 for idx in range(len(date_list))]
t = {}

for idx in risk_asset:
    t[idx] = init_list

t['Date'] = date_list

risk_price = pd.DataFrame.from_dict(t);
risk_price = risk_price.set_index('Date')
risk_momentum = pd.DataFrame.from_dict(t);
risk_momentum = risk_momentum.set_index('Date')

# 다 가져 와서, 긴 것 위무로 만들고 나머지 다 0
def cal_momentum(x):
    print(x)
    return_v = (x[-1] - x[-2]) * 12 + 4 * (x[-1] - x[-4]) + 2 * (x[-1] - x[-7]) + x[0]
    return return_v

for idx in risk_asset:
    try:
        v = fdr.DataReader(idx, start_date, end_date).resample('M').last()
        #print(v)
        v.drop(['Open', 'High', 'Low', 'Volume', 'Change'], axis=1, inplace=True)
        #print(v)
        #print(type(v))
        print(v.columns)
        v.columns = [idx]
        print(v)
        risk_price.update(v)
        print(risk_price)
        mom = v.rolling(window=12).apply(lambda x: cal_momentum(x))
        risk_momentum.update(mom)
        print(risk_momentum)
    except Exception as e:
        print(e)
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
