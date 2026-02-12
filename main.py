import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# 1. Render အတွက် Web Server တည်ဆောက်ခြင်း
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live with Permanent Memory (Gemini 2.5)!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 2. API Keys နှင့် Database ချိတ်ဆက်ခြင်း
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_KEY)

# --- ဒီနေရာမှာ ၂.၅ ကို ပြန်ပြောင်းထားပေးပါတယ် ---
model = genai.GenerativeModel('gemini-2.5-flash')

# MongoDB Database ချိတ်ဆက်ခြင်း
client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

# 3. Message Handling (Memory စနစ်ပါဝင်သည်)
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    
    # Database ထဲကနေ အရင်ပြောထားတဲ့ History ကို ဖတ်ယူမယ်
    user_data = history_collection.find_one({"user_id": user_id})
    history = user_data['history'] if user_data else []

    try:
        # Gemini Chat Session ကို History အဟောင်းဖြင့် စတင်ခြင်း
        chat_session = model.start_chat(history=history)
        
        # Gemini ဆီက အဖြေတောင်းခြင်း
        response = chat_session.send_message(message.text)
        
        if response.text:
            # အဖြေရလျှင် History အသစ်ကို Database ထဲမှာ Update လုပ်မယ်
            new_history = chat_session.history
            
            # နောက်ဆုံး စာကြောင်း ၃၀ ပဲ သိမ်းမယ်
            if len(new_history) > 30:
                new_history = new_history[-30:]
                
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
            
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Gemini က အဖြေမထုတ်ပေးနိုင်ပါဘူးခင်ဗျာ။")
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            bot.reply_to(message, "Quota ပြည့်သွားပါပြီ။ ၁ မိနစ်လောက်နေမှ ပြန်မေးပေးပါခင်ဗျာ။")
        else:
            bot.reply_to(message, f"Error တက်နေပါတယ်ခင်ဗျာ:\n{error_str}")

# 4. Bot ကို စတင် Run ခြင်း
def start_bot():
    Thread(target=run).start()
    print("Bot is starting with Gemini 2.5 Flash and Memory...")
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
