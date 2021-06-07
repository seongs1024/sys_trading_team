from sqlalchemy import create_engine
import pymysql
import pandas as pd
import OpenDartReader
from pykrx import stock
import string
import time

pymysql.install_as_MySQLdb()

api_key = '' # use your api key
dart = OpenDartReader(api_key)

df = pd.read_excel('우선주.xlsx')
upper_code = df['Symbol']
upper_all_code = []
for code in upper_code:
    upper_all_code.append(code[1:])

all_code_name = stock.get_market_ticker_list(market='KOSPI')
code_list = set(all_code_name) - set(upper_all_code)

conn = pymysql.connect(host='127.0.0.1', user='root', password='7385', db='annual_finance_data', charset='utf8')
curs = conn.cursor()
sql = 'SHOW TABLES'
curs.execute(sql)
result = curs.fetchall()

all_code = []
for code in result:
    code = list(code)
    all_code.append(code)

fail_list = []

for code in code_list:
    stock_name = stock.get_market_ticker_name(code)

    if [stock_name.lower()] in all_code:
        print(stock_name, 'Exists')
        continue

    year_list = [2017,2020]
    long_data = []
    # try:
    for year in year_list:
        try:
            df = dart.finstate(code, year, reprt_code=11011)  # 1분기 : 11013, 반기보고서 : 11012, 3분기 : 11014, 사업보고서 : 11011
            df = pd.DataFrame(df)

            drop_list = ['rcept_no', 'reprt_code', 'bsns_year', 'corp_code', 'stock_code', 'fs_div', 'sj_div',
                         'thstrm_nm', 'frmtrm_nm', 'frmtrm_dt', 'bfefrmtrm_nm', 'bfefrmtrm_dt', 'ord', 'thstrm_dt']

            df = df.drop(drop_list, axis=1)

            df.set_index('fs_nm', inplace=True)

            if '연결재무제표' not in df.index:
                cond = df.index == '재무제표'
            else:
                cond = df.index == '연결재무제표'

            df = df[cond]
            del df['sj_nm']

            df.rename(columns={"account_nm": '계정', 'thstrm_amount': str(year), 'frmtrm_amount': str(year - 1),
                               'bfefrmtrm_amount': str(year - 2)}, inplace=True)
            df = df.reset_index()
            del df['fs_nm']

            df[str(year)] = df[str(year)].str.replace(',', '').astype('int64') / 100000000
            df[str(year - 1)] = df[str(year - 1)].str.replace(',', '').astype('int64') / 100000000
            df[str(year - 2)] = df[str(year - 2)].str.replace(',', '').astype('int64') / 100000000
            df[str(year)] = round(df[str(year)])
            df[str(year - 1)] = round(df[str(year - 1)])
            df[str(year - 2)] = round(df[str(year - 2)])

            df = df[['계정', str(year-2), str(year - 1), str(year)]]
            df.set_index('계정', inplace=True)

            long_data.append(df)

            df = pd.concat(long_data, axis=1)

            if len(df.index) == 0:
                continue
        except:
            continue

    df = df.reset_index()

    engine = create_engine("mysql+mysqldb://root:7385@127.0.0.1/annual_finance_data", encoding='utf-8')
    conn = engine.connect()
    df.to_sql(name=stock_name, con=conn, if_exists='replace')
    print(stock_name, 'SUCCESS')


    time.sleep(1.5)

fail_list = pd.DataFrame(fail_list)
fail_list.to_excel('코스닥 실패.xlsx')
