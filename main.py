import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# 1. Render Web Server (Bot မအိပ်အောင် လုပ်ဆောင်ချက်)
app = Flask('')
@app.route('/')
def home(): return "Lawkanat Bot Gemini 2.5 is Live!"

def run(): app.run(host='0.0.0.0', port=8080)

# 2. Setup API Keys & Database
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

# Gemini 2.5 Flash Configuration
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction="မင်းက 'လောကနတ် Bot' ဖြစ်ပါတယ်။ မြန်မာလို ယဉ်ကျေးစွာ ဖြေကြားပေးပါ။"
)

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

# 3. Message Handling Logic
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    user_data = history_collection.find_one({"user_id": user_id})
    raw_history = user_data['history'] if user_data else []

    try:
        # Chat Session စတင်ခြင်း
        chat_session = model.start_chat(history=raw_history)
        response = chat_session.send_message(message.text)
        
        if response.text:
            # Memory သိမ်းဆည်းရန် Format ပြင်ခြင်း
            new_history = []
            for content in chat_session.history:
                new_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # Quota သက်သာစေရန် နောက်ဆုံး ၆ ကြောင်းသာ သိမ်းဆည်းမည်
            if len(new_history) > 6:
                new_history = new_history[-6:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
            bot.reply_to(message, response.text)
            
    except Exception as e:
        # Error တက်ရင် ဘာကြောင့်လဲဆိုတာ တိုက်ရိုက်ပြပါမယ်
        bot.reply_to(message, f"စနစ်ချို့ယွင်းချက် - {str(e)}")

# 4. Starting the Bot
def start_bot():
    Thread(target=run).start()
    print("Bot is booting up with Gemini 2.5 Flash...")
    bot.remove_webhook()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
