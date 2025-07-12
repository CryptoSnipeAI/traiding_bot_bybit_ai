import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from features import prepare_features
from data_fetch import get_klines
from get_pairs import get_top_pairs

def main():
    symbols = get_top_pairs()
    all_features = []
    all_targets = []

    for symbol in symbols:
        print(f"📈 Обработка: {symbol}")
        try:
            df = get_klines(symbol)
            result = prepare_features(df)

            # если prepare_features вернул None
            if result is None:
                print(f"⚠️ {symbol}: фичи не рассчитаны")
                continue

            df_feat, target = result

            if df_feat is None or df_feat.empty:
                print(f"⚠️ {symbol}: нет данных после подготовки")
                continue

            # Убираем ненужные колонки
            drop_cols = ['timestamp', 'open', 'high', 'low', 'turnover', 'future_max', 'return', 'target']
            X = df_feat.drop(columns=[col for col in drop_cols if col in df_feat.columns])
            y = target if isinstance(target, pd.Series) else df_feat['target']

            all_features.append(X)
            all_targets.append(y)

        except Exception as e:
            print(f"❌ Ошибка при обработке {symbol}: {e}")
            continue

    if not all_features:
        raise ValueError("Нет данных для обучения. Все тикеры не прошли фильтр.")

    # Объединяем данные всех монет
    X_all = pd.concat(all_features)
    y_all = pd.concat(all_targets)

    # Обучение модели
    X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Оценка модели
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print("📊 Accuracy:", round(acc, 4))
    print(classification_report(y_test, y_pred))

    # Сохраняем модель
    joblib.dump(model, "model.pkl")
    print("✅ Модель сохранена: model.pkl")

if __name__ == "__main__":
    main()
