import telebot

TOKEN = "8656789314:AAGOGDKuiBhGetGTkbC__oL-BE6eAcJxGKw"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Olá! Meu bot de achadinhos está rodando 24h na nuvem 🚀")

print("Bot iniciado...")
bot.infinity_polling()
