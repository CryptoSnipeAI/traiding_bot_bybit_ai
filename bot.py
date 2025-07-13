# bot.py
import os
import joblib
from data_fetch import get_klines
from features import prepare_features as prepare
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from get_pairs import get_top_pairs

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = joblib.load("model.pkl")

def analyze(symbol, model):
    try:
        print(f"📈 Обработка: {symbol}")
        df = get_klines(symbol, limit=500)
        if df is None or df.empty:
            raise ValueError("Нет данных с биржи")

        df, _ = prepare(df)
        if df is None or df.empty:
            raise ValueError("Нет фичей после подготовки")

        drop_cols = ['timestamp', 'open', 'high', 'low', 'turnover', 'future_max', 'return', 'target']
        feature_columns = [col for col in df.columns if col not in drop_cols]

        last = df[feature_columns].iloc[[-1]]
        if last.shape[1] != model.n_features_in_:
            raise ValueError(f"Feature shape mismatch: expected {model.n_features_in_}, got {last.shape[1]}")

        pred = model.predict(last)[0]
        prob = model.predict_proba(last)[0][pred]
        entry = df['close'].iloc[-1]
        sl = entry * (0.995 if pred else 1.005)
        tp = entry * (1.01 if pred else 0.99)
        direction = "LONG" if pred else "SHORT"

        return f"{symbol}\n{direction} @ {entry:.2f}\nSL {sl:.2f} / TP {tp:.2f}\nConf: {prob*100:.1f}%"

    except Exception as e:
        print(f"❌ {symbol} error: {e}")
        return None

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Команда /signal получена")
    pairs = get_top_pairs()
    print(f"🔍 Получены пары: {pairs}")
    best_signal = None
    best_prob = 0

    for symbol in pairs:
        print(f"📊 Анализ: {symbol}")
        signal = analyze(symbol, model)
        print(f"➡️ Результат: {signal}")
        if signal:
            try:
                prob_line = signal.split("Conf: ")[-1]
                prob = float(prob_line.replace('%', ''))
                if prob > best_prob:
                    best_prob = prob
                    best_signal = signal
            except Exception as e:
                print(f"❌ Prob parsing error: {e}")

    if best_signal:
        await update.message.reply_text(best_signal)
    else:
        await update.message.reply_text("❌ Нет подходящих сигналов")

def send_auto_signal():
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    pairs = get_top_pairs()
    best_signal = None
    best_prob = 0

    for symbol in pairs:
        signal = analyze(symbol, model)
        if signal:
            try:
                prob_line = signal.split("Conf: ")[-1]
                prob = float(prob_line.replace('%', ''))
                if prob > best_prob:
                    best_prob = prob
                    best_signal = signal
            except Exception as e:
                print(f"❌ Prob parsing error: {e}")

    if best_signal:
        bot.send_message(chat_id=CHAT_ID, text=best_signal)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_cmd))

    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(send_auto_signal, 'interval', minutes=15)
    scheduler.start()

    print("✅ Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
