import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Render အတွက် Web Server တည်ဆောက်ခြင်း
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run():
    # Render က Port 8080 ကို အသုံးပြုဖို့ လိုအပ်ပါတယ်
    app.run(host='0.0.0.0', port=8080)

# 2. API Keys များ ချိတ်ဆက်ခြင်း
# Render Environment Variables ထဲမှာ ထည့်ထားတဲ့ နာမည်တွေနဲ့ တူရပါမယ်
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI ကို Configure လုပ်ခြင်း
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TOKEN)

# 3. Message Handling (စာပြန်မည့်အပိုင်း)
@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        # Gemini ဆီက အဖြေတောင်းခြင်း
        response = model.generate_content(message.text)
        
        # အကယ်၍ Gemini က အဖြေထုတ်ပေးရင် ပြန်ပို့မယ်
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Gemini က အဖြေမထုတ်ပေးနိုင်ပါဘူးခင်ဗျာ။")
            
    except Exception as e:
        # Error တက်ရင် ဘာကြောင့်လဲဆိုတာကို Telegram မှာ ပြပေးမယ်
        error_msg = f"Error တက်နေပါတယ်ခင်ဗျာ:\n{str(e)}"
        bot.reply_to(message, error_msg)

# 4. Bot ကို စတင် Run ခြင်း
def start_bot():
    # Web server ကို Background မှာ Run မယ်
    Thread(target=run).start()
    print("Bot is starting and connecting to Telegram...")
    # Telegram Bot ကို စတင်နိုးကြားစေမယ်
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
