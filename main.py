import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Render အတွက် Web Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run():
    # Render က Port 8080 ကို အသုံးပြုဖို့ လိုအပ်ပါတယ်
    app.run(host='0.0.0.0', port=8080)

# 2. API Keys များ
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TOKEN)

# 3. Message Handling
@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        response = model.generate_content(message.text)
        
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Gemini က အဖြေမထုတ်ပေးနိုင်ပါဘူးခင်ဗျာ။")
            
    except Exception as e:
        error_msg = f"Error တက်နေပါတယ်ခင်ဗျာ:\n{str(e)}"
        bot.reply_to(message, error_msg)

# 4. Bot ကို စတင် Run ခြင်း
def start_bot():
    Thread(target=run).start()
    print("Bot is starting and connecting to Telegram...")
    # 409 Conflict ဖြစ်တာကို ကာကွယ်ဖို့ Webhook ကို အရင်ဖြုတ်မယ်
    bot.remove_webhook()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
