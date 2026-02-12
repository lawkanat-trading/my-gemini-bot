import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# 1. Render Web Server
app = Flask('')
@app.route('/')
def home(): return "Lawkanat Bot is Online!"

def run(): app.run(host='0.0.0.0', port=8080)

# 2. Setup Keys & Database
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

genai.configure(api_key=GEMINI_KEY)

# Free Tier မှာ အငြိမ်ဆုံးဖြစ်တဲ့ Gemini 1.5 Flash ကို သုံးပါမယ်
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="You are Lawkanat Bot. Respond in Burmese. Remember user context from history."
)

client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

# 3. Message Handler
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    user_data = history_collection.find_one({"user_id": user_id})
    raw_history = user_data['history'] if user_data else []

    try:
        chat_session = model.start_chat(history=raw_history)
        response = chat_session.send_message(message.text)
        
        if response.text:
            # Memory သိမ်းဆည်းခြင်း
            updated_history = []
            for content in chat_session.history:
                updated_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # Quota သက်သာအောင် နောက်ဆုံး ၆ ကြောင်း (၃ စုံ) ပဲ သိမ်းပါမယ်
            if len(updated_history) > 6:
                updated_history = updated_history[-6:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": updated_history}},
                upsert=True
            )
            bot.reply_to(message, response.text)
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            bot.reply_to(message, "API Limit ပြည့်သွားပါပြီ။ ၁ မိနစ်လောက်နားပြီးမှ ပြန်မေးပေးပါ။")
        elif "Conflict" in error_msg:
            print("Multiple instances detected. Polling will handle this.")
        else:
            bot.reply_to(message, f"စနစ်ချို့ယွင်းချက် - {error_msg[:100]}")

# 4. Run Bot
def start_bot():
    Thread(target=run).start()
    print("Bot is starting with Gemini 1.5 Flash...")
    # restart ချရင် Conflict မဖြစ်အောင် သေချာစစ်ဆေးပါမယ်
    bot.remove_webhook()
    bot.polling(non_stop=True, timeout=60)

if __name__ == "__main__":
    start_bot()
