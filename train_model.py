import os
import joblib
import pandas as pd
from xgboost import XGBClassifier
from data_fetch import get_klines, get_all_symbols
from features import prepare

def train_model(symbol):
    try:
        df = get_klines(symbol)
        df.to_csv(f"market_data/{symbol}.csv", index=False)
        X, y = prepare(df)
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        model.fit(X, y)
        joblib.dump(model, f"models/{symbol}_xgb.pkl")
        print(f"✔️ {symbol} model saved")
    except Exception as e:
        print(f"⚠️ Error with {symbol}: {e}")

if __name__ == "__main__":
    os.makedirs("models", exist_ok=True)
    os.makedirs("market_data", exist_ok=True)
    for sym in get_all_symbols():
        train_model(sym)