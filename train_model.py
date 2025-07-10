import joblib
import pandas as pd
import numpy as np
from features import prepare_features
from utils import fetch_klines
from sklearn.ensemble import RandomForestClassifier

symbols = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LTCUSDT'
]

all_X, all_y = [], []

for symbol in symbols:
    try:
        df = fetch_klines(symbol, '15m', 200)
        X = prepare_features(df)
        y = (df['close'].shift(-1).iloc[X.index] > df['close'].iloc[X.index]).astype(int)
        all_X.append(X)
        all_y.append(y)
        print(f'✅ {symbol} готов')
    except Exception as e:
        print(f'❌ {symbol} ошибка: {e}')

X_all = pd.concat(all_X, ignore_index=True)
y_all = pd.concat(all_y, ignore_index=True)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_all, y_all)

joblib.dump(model, 'model.pkl')
print("✅ Модель обучена и сохранена как model.pkl")

model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, use_label_encoder=False, eval_metric="logloss")
model.fit(X_all, y_all)

joblib.dump(model, "model.pkl")
print("✅ Модель обучена и сохранена как model.pkl")
