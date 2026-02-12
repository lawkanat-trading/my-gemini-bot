import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

app = Flask('')
@app.route('/')
def home(): return "Lawkanat Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)

TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are Lawkanat Bot. Answer in Burmese. Keep it short."
)

client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    user_data = history_collection.find_one({"user_id": user_id})
    raw_history = user_data['history'] if user_data else []

    try:
        # Gemini Chat စတင်ခြင်း
        chat_session = model.start_chat(history=raw_history)
        response = chat_session.send_message(message.text)
        
        if response.text:
            # History ကို Database သိမ်းရန် Format ပြင်ခြင်း
            updated_history = []
            for content in chat_session.history:
                updated_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # Quota သက်သာရန် နောက်ဆုံး ၆ ကြောင်း (၃ စုံ) သာ သိမ်းမည်
            if len(updated_history) > 6:
                updated_history = updated_history[-6:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": updated_history}},
                upsert=True
            )
            bot.reply_to(message, response.text)
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            bot.reply_to(message, "API Limit ပြည့်သွားပါပြီ။ ၁ နာရီလောက်နားပြီးမှ ပြန်မေးပေးပါ။")
        else:
            # Error အစစ်အမှန်ကို Telegram မှာ ပြခိုင်းခြင်း
            bot.reply_to(message, f"စနစ်ချို့ယွင်းချက်တက်နေသည်- {error_str[:150]}")

def start_bot():
    Thread(target=run).start()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
