# get_pairs.py
import os
import joblib
import pandas as pd
from data_fetch import get_klines
from features import prepare
from xgboost import XGBClassifier
from get_pairs import get_top_pairs

pairs = get_top_pairs()

all_X, all_y = [], []

for symbol in pairs:
    try:
        df = get_klines(symbol, limit=500)
        X, y = prepare(df)
        all_X.append(X)
        all_y.append(y)
        print(f"✅ {symbol} готов")
    except Exception as e:
        print(f"❌ {symbol} ошибка: {e}")

X = pd.concat(all_X)
y = pd.concat(all_y)

model = XGBClassifier(n_estimators=100, max_depth=3)
model.fit(X, y)
joblib.dump(model, "model.pkl")
print("✅ Модель обучена и сохранена как model.pkl")
