import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# Web Server (Render အတွက်)
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Keys များ (Render Env Variables ထဲကအတိုင်း)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini Setup (Stable ဖြစ်တဲ့ gemini-pro ကို သုံးပါမယ်)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # Error ပြန်ပို့မယ့်စာ
        bot.reply_to(message, f"Error: {str(e)}")

def start_bot():
    Thread(target=run).start()
    bot.polling(non_stop=True)

if __name__ == "__main__":
    start_bot()
