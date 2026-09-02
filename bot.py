import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Pega o token de forma segura direto das Variáveis de Ambiente do Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Servidor web simples para o Render não dar Timeout
app = Flask('')

@app.route('/')
def home():
    return "Bot Casify rodando com sucesso!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Menus e Funções do Bot
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton("🎁 Criar Oferta", callback_data="btn_promocao")
    b2 = InlineKeyboardButton("🔍 Buscar", callback_data="btn_buscar")
    b3 = InlineKeyboardButton("🔗 Enviar Link", callback_data="btn_enviar_link")
    b4 = InlineKeyboardButton("📊 Meu Plano", callback_data="btn_plano")
    b5 = InlineKeyboardButton("🔑 API Shopee", callback_data="btn_api")
    b6 = InlineKeyboardButton("🛠️ Suporte", callback_data="btn_suporte")
    markup.add(b1, b2, b3, b4, b5, b6)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 **Casify - Painel**\n\n"
        "Envie o seu link da Shopee para gerar a oferta no padrão profissional de descontos e Pix!\n\n"
        "👇 **Escolha uma opção abaixo:**"
    )
    bot.send_message(message.chat.id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_promocao":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎁 Envie o link do produto para transformarmos em oferta:")
    elif call.data == "btn_buscar":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔍 Digite o nome do produto que deseja buscar:")
    elif call.data == "btn_enviar_link":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔗 Cole o seu link bruto da Shopee aqui.")
    elif call.data == "btn_plano":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Plano Atual: Gratuito 🚀")
    elif call.data == "btn_api":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 API da Shopee pendente. Usando links manuais por enquanto.")
    elif call.data == "btn_suporte":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛠️ Suporte técnico à disposição!")

@bot.message_handler(func=lambda message: True)
def formatar_oferta(message):
    link_original = message.text.strip()
    if "http://" in link_original or "https://" in link_original:
        link_afiliado = f"{link_original}?uls_trackid=seu_codigo_aqui"
        
        # Estrutura completa atualizada com a marca Casify
        texto_postagem = (
            "PRECISAVA DESSA NO GARIMPO 🤌\n\n"
            "✅ Kit 5 Camisetas Masculinas Slim Básicas\n\n"
            "DE ~~R$ 239,00~~~\n"
            "🔥 **POR R$ 112,29** 🔥 (53% OFF) no PIX\n\n"
            "✨ *Casify*"
        )
        
        markup = InlineKeyboardMarkup()
        botao_comprar = InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado)
        markup.add(botao_comprar)
        
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Digite `/menu` para abrir o painel ou envie um link válido.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot Casify iniciado...")
    bot.infinity_polling()
