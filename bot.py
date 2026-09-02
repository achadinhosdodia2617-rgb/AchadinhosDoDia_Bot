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
    return "Bot de Achadinhos Profissional rodando!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Menus e Funções do Bot
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton("🎁 Criar Promoção", callback_data="btn_promocao")
    b2 = InlineKeyboardButton("🔍 Buscar Produto", callback_data="btn_buscar")
    b3 = InlineKeyboardButton("🔗 Enviar Link", callback_data="btn_enviar_link")
    b4 = InlineKeyboardButton("📊 Meu Plano", callback_data="btn_plano")
    b5 = InlineKeyboardButton("🔑 Cadastrar API", callback_data="btn_api")
    b6 = InlineKeyboardButton("🛠️ Suporte", callback_data="btn_suporte")
    markup.add(b1, b2, b3, b4, b5, b6)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 **Painel de Automação - Achadinhos**\n\n"
        "Seu sistema profissional de conversão de links e vendas está ativo.\n\n"
        "👇 **Escolha uma opção no painel abaixo:**"
    )
    bot.send_message(message.chat.id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_promocao":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎁 Envie o link do produto da Shopee para transformarmos em uma oferta profissional:")
    elif call.data == "btn_buscar":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔍 Digite o nome do produto que deseja pesquisar:")
    elif call.data == "btn_enviar_link":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔗 Cole o seu link bruto aqui para gerarmos a estrutura de afiliado.")
    elif call.data == "btn_plano":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Plano Atual: Gratuito / Base Ativa 🚀")
    elif call.data == "btn_api":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 Aguardando liberação da API da Shopee para automação total de buscas.")
    elif call.data == "btn_suporte":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛠️ Suporte técnico pronto para te ajudar!")

@bot.message_handler(func=lambda message: True)
def formatar_oferta(message):
    link_original = message.text.strip()
    if "http://" in link_original or "https://" in link_original:
        link_afiliado = f"{link_original}?uls_trackid=seu_codigo_aqui"
        
        # Estrutura profissional baseada em gatilhos mentais e psicologia de vendas
        texto_postagem = (
            "🔥 **ACHADINHO IMPERDÍVEL!** 🔥\n\n"
            "📦 *Selecionado a dedo para o nosso canal.*\n"
            "✨ *Qualidade garantida e excelente custo-benefício para facilitar o seu dia a dia.*\n\n"
            "❌ De: ~~R$ 129,90~~~\n"
            "💥 **Por apenas: R$ 59,90** *(54% OFF)*\n"
            "💳 Parcelamento facilitado disponível no site!\n\n"
            "🏃‍♂️ *Corre que o estoque promocional costuma acabar rápido!*"
        )
        
        markup = InlineKeyboardMarkup()
        botao_comprar = InlineKeyboardButton("🛒 GARANTIR MEU DESCONTO", url=link_afiliado)
        markup.add(botao_comprar)
        
        # Exemplo simulando o envio com foto (quando a API estiver ativa, puxaremos a imagem real do produto)
        # Por enquanto, enviamos a mensagem estruturada com o botão de alta conversão:
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Comando não reconhecido. Digite `/menu` para abrir o painel principal ou envie um link válido da Shopee.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot profissional iniciado com sucesso...")
    bot.infinity_polling()
