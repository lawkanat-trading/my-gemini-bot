import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# 1. Render အတွက် Web Server Setup
app = Flask('')
@app.route('/')
def home(): return "Lawkanat Bot is Live!"

def run(): app.run(host='0.0.0.0', port=8080)

# 2. Environment Variables ယူခြင်း
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

# Gemini Configuration (အငြိမ်ဆုံး version နဲ့ ချိတ်ပါမယ်)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are Lawkanat Bot. Answer in Burmese clearly and concisely."
)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

# 3. Message Logic
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    user_data = history_collection.find_one({"user_id": user_id})
    raw_history = user_data['history'] if user_data else []

    try:
        # History ကို Gemini format အမှန်အတိုင်း ပြောင်းလဲခြင်း
        formatted_history = []
        for h in raw_history:
            formatted_history.append({
                "role": h["role"],
                "parts": [{"text": p["text"]} for p in h["parts"]]
            })

        chat_session = model.start_chat(history=formatted_history)
        response = chat_session.send_message(message.text)
        
        if response.text:
            new_history = []
            for content in chat_session.history:
                new_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # Quota သက်သာအောင် နောက်ဆုံး ၆ ကြောင်းပဲ သိမ်းမယ်
            if len(new_history) > 6:
                new_history = new_history[-6:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
            bot.reply_to(message, response.text)
            
    except Exception as e:
        bot.reply_to(message, f"စနစ်ချို့ယွင်းချက် - {str(e)}")

# 4. Starting the Bot
def start_bot():
    Thread(target=run).start()
    bot.remove_webhook() # Conflict မဖြစ်အောင် Webhook အဟောင်းဖြုတ်မယ်
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
