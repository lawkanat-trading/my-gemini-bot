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
    return "Lawkanat Bot is Online with Memory!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 2. API Keys နှင့် Database ချိတ်ဆက်ခြင်း
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
MONGO_URI = os.environ.get('MONGO_URI')

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_KEY)

# Bot ကို Smart ဖြစ်စေရန် System Instruction ထည့်သွင်းခြင်း
instruction = "You are Lawkanat Bot. Always remember the user's name and chat details from history. Speak naturally in Burmese."
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=instruction
)

# MongoDB Database ချိတ်ဆက်ခြင်း
client = MongoClient(MONGO_URI)
db = client['gemini_bot_db']
history_collection = db['chat_histories']

bot = telebot.TeleBot(TOKEN)

# 3. Message Handling (ထာဝရမှတ်ဉာဏ်စနစ်)
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = str(message.from_user.id)
    
    # Database ထဲမှ အရင်ပြောထားသော History ကို ဆွဲထုတ်ခြင်း
    user_data = history_collection.find_one({"user_id": user_id})
    raw_history = user_data['history'] if user_data else []

    try:
        # Gemini Chat Session ကို History အဟောင်းဖြင့် စတင်ခြင်း
        chat_session = model.start_chat(history=raw_history)
        
        # အဖြေတောင်းခြင်း
        response = chat_session.send_message(message.text)
        
        if response.text:
            # History အသစ်ကို Database တွင် သိမ်းဆည်းရန် Format ပြင်ခြင်း
            updated_history = []
            for content in chat_session.history:
                updated_history.append({
                    "role": content.role,
                    "parts": [{"text": part.text} for part in content.parts]
                })
            
            # Memory အရမ်းမများစေရန် နောက်ဆုံး စာကြောင်း ၄၀ ခန့်သာ သိမ်းမည်
            if len(updated_history) > 40:
                updated_history = updated_history[-40:]
                
            # Database တွင် Update လုပ်ခြင်း
            history_collection.update_one(
                {"user_id": user_id},
                {"$set": {"history": updated_history}},
                upsert=True
            )
            
            bot.reply_to(message, response.text)
            
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            bot.reply_to(message, "ခဏလေးစောင့်ပေးပါ၊ လူများနေလို့ပါ။")
        else:
            bot.reply_to(message, f"စနစ်ချို့ယွင်းချက် - {error_str}")

# 4. Bot ကို စတင် Run ခြင်း
def start_bot():
    Thread(target=run).start()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
