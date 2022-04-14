from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import random

# フロントから送信されたデータの型
class Item(BaseModel):
    invest_type: str
    start_value: int
    withdrawal: int
    min_years: int
    most_likely_years: int
    max_years: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],      
    allow_headers=["*"])


def read(file_name):

    """事前準備として投資商品の年間利回りやインフレ率のデータが入ったファイルを開き、小数に変換してリストを返す"""

    with open(file_name,encoding="utf-8_sig") as in_file:
        lines = [float(line.strip()) for line in in_file]
        decimal = [round(line / 100, 5) for line in lines]
        return decimal

"""注意: 入力データファイルはパーセント形式です"""

try:
        bonds = read('10yrUSBondReturns1969to2021.txt')
        sp500 = read('SP500Returns1969to2021.txt')
        nikkei = read('NIKKEIReturns1969to2021.txt')
        gold = read('GOLDReturns1969to2021.txt')
        infl_rate = read('annualUSInflation1969to2021.txt')
except IOError as e :
        sys.exit(1)

# ヘルスチェック用
@app.get("/")
async def health():
    return {"status": "OK"}

@app.post("/fire/")
async def cal_bonds(data: Item):
    invest_type = data.invest_type
    start_value = data.start_value
    withdrawal = data.withdrawal
    min_years = data.min_years
    most_likely_years = data.most_likely_years
    max_years = data.max_years
    # フロントから送信された初期資金、年間生活費、引退生活の最小、最頻、最大年数の情報を受け取る

                
    """モンテカルロシミュレーションのループを実行し、「引退生活終了時」の残高と破産回数を調べる"""
    case_count = 0
    bankrupt_count = 0
    outcome = []
    
    # ユーザーが選択した投資の対象に応じて、計算に使用する過去の市場データを変える
    # 5つの場合分け
    # 米国10年国債、米国株SP500、日経平均株価、金投資、その他(異常値)    
    if invest_type == "bonds":
        invest = bonds
    elif invest_type == "sp500": 
        invest = sp500
    elif invest_type == "nikkei":
        invest = nikkei
    elif invest_type == "gold":
        invest = gold    
      # 投資の対象が4つのうち、どれでもない(異常値)場合
    else:
        sys.exit(1)

    while case_count < int(50000):
        investments = int(start_value)
        start_year = random.randrange(0, len(invest))
        duration = int(random.triangular(int(min_years), int(max_years),int(most_likely_years)))
        end_year = start_year + duration
        lifespan = [i for i in range(start_year, end_year)]
        bankrupt = 'no'
        
        # 各ケースの一時リストを作る
        lifespan_returns = []
        lifespan_infl = []
        for i in lifespan:
            lifespan_returns.append(invest[i % len(invest)])
            lifespan_infl.append(infl_rate[i % len(infl_rate)])
        
        # 各ケースで引退生活の各年をループする
        for index, i in enumerate(lifespan_returns):
            infl = lifespan_infl[index]
            
            # 最初の年はインフレの調節をしない
            if index == 0:
                withdraw_infl_adj = int(withdrawal)
            else:
                withdraw_infl_adj = int(withdraw_infl_adj * (1+infl))
                
            investments -= withdraw_infl_adj
            investments = int(investments * (1+i))
            
            if investments <= 0:
                bankrupt = 'yes'
                break
            
        if bankrupt == 'yes':
            outcome.append(0)
            bankrupt_count += 1
        else:
            outcome.append(investments)
            
        case_count += 1

    else:
        pass    
        """モンテカルロシミュレーション、ループ処理ここで終わり"""
 
 
    """シミュレーションの結果から資金が尽きる確率を計算する"""
    total = len(outcome)
    odds = round(100 * bankrupt_count / total, 1)

    """結果のグラフ描画用データを用意する"""
    plotdata = outcome[:200] # 最初の200回の結果データ

        
    """フロントへ計算結果をデータ送信(資金が尽きる確率、平均、最小、最大結果、グラフ用データ)"""
    return[odds,int(sum(outcome) / total),min(i for i in outcome),max(i for i in outcome),*plotdata]
