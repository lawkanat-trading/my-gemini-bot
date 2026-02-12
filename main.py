import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

app = Flask('')
@app.route('/')
def home(): return "Lawkanat Bot is Running!"

def run(): app.run(host='0.0.0.0', port=8080)

# API & Database Keys
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', # Quota ပိုများသော 1.5-flash ကို သုံးရန် အကြံပြုပါသည်
    system_instruction="You are Lawkanat Bot. Keep answers concise to save quota. Remember user context."
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
        chat_session = model.start_chat(history=raw_history)
        response = chat_session.send_message(message.text)
        
        if response.text:
            updated_history = []
            for content in chat_session.history:
                updated_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # --- Quota ချွေတာရန် History ကို ၁၀ ကြောင်းသာ သိမ်းမည် ---
            if len(updated_history) > 10:
                updated_history = updated_history[-10:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": updated_history}},
                upsert=True
            )
            bot.reply_to(message, response.text)
            
except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            bot.reply_to(message, "Gemini API Limit ပြည့်သွားပါပြီ။ ခဏနားပြီးမှ ပြန်မေးပေးပါ။")
        elif "409" in error_msg:
            # ဒီနေရာမှာ Conflict ဖြစ်ရင် ဘာမှပြန်မလုပ်ဘဲ ကျော်သွားခိုင်းတာက ပိုငြိမ်ပါတယ်
            print("Conflict Error: Multiple instances running.")
        else:
            # တခြား Error ဆိုရင် ဘာ Error လဲဆိုတာ Telegram မှာ တိုက်ရိုက်ပြခိုင်းပါ
            bot.reply_to(message, f"စနစ်ချို့ယွင်းချက်- {error_msg[:100]}")

def start_bot():
    Thread(target=run).start()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
