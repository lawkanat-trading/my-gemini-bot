import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# 1. Render မှာ အမြဲတမ်း အလုပ်လုပ်နေစေဖို့ Web Server ဆောက်ခြင်း
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 2. Keys များအား Environment Variables မှ ဆွဲယူခြင်း
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Configuration (အမြန်ဆုံးဖြစ်တဲ့ 1.5-flash ကို သုံးထားပါတယ်)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Telegram Bot Setup
bot = telebot.TeleBot(TOKEN)

# 3. Message Handling (စာသားလက်ခံပြီး Gemini နဲ့ ပြန်ဖြေခြင်း)
@bot.message_handler(func=lambda message: True)
def chat_with_gemini(message):
    try:
        # Gemini ဆီမှ အဖြေတောင်းခြင်း
        response = model.generate_content(message.text)
        
        # အဖြေပြန်ပို့ခြင်း
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "Gemini က အဖြေမထုတ်ပေးနိုင်ပါဘူး။")
            
    except Exception as e:
        # အမှားတက်ပါက Error Message ကို Telegram တွင် ပြသရန်
        error_info = f"Error တက်နေပါတယ်ခင်ဗျာ:\n{str(e)}"
        bot.reply_to(message, error_info)

# 4. Bot ကို စတင်အသက်သွင်းခြင်း
def start_bot():
    # Flask Server ကို သီးခြား Thread တစ်ခုဖြင့် Run ရန်
    Thread(target=run).start()
    print("Bot is starting...")
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
