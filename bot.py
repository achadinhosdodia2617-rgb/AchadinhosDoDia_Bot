import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8656789314:AAGOGDKuiBhGetGTkbC__oL-BE6eAcJxGKw"
bot = telebot.TeleBot(TOKEN)

# Função para criar o Menu principal com botões estilizados (estilo Promovy)
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton("🎁 Promoção", callback_data="btn_promocao")
    b2 = InlineKeyboardButton("🔍 Buscar", callback_data="btn_buscar")
    b3 = InlineKeyboardButton("🔗 Enviar Link", callback_data="btn_enviar_link")
    b4 = InlineKeyboardButton("📊 Meu Plano", callback_data="btn_plano")
    b5 = InlineKeyboardButton("🔑 Cadastrar API", callback_data="btn_api")
    b6 = InlineKeyboardButton("🛠️ Suporte", callback_data="btn_suporte")
    markup.add(b1, b2, b3, b4, b5, b6)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 **Painel Principal - Achadinhos**\n\n"
        "Acompanhe suas promoções e gerencie seus links de afiliado por aqui.\n\n"
        "👇 **Escolha uma opção abaixo:**"
    )
    bot.send_message(message.chat.id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

# Responde aos cliques nos botões do menu
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_promocao":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎁 Envie o link do produto que deseja transformar em promoção:")
    elif call.data == "btn_buscar":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔍 Digite o nome do produto que deseja buscar:")
    elif call.data == "btn_enviar_link":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔗 Cole o seu link bruto da Shopee aqui para gerarmos o link com seu afiliado.")
    elif call.data == "btn_plano":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Você está utilizando o plano gratuito do seu bot de achadinhos 🚀")
    elif call.data == "btn_api":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 Para cadastrar sua API da Shopee, digite o comando `/cadastrar` seguido do seu AppID e Senha.")
    elif call.data == "btn_suporte":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛠️ Suporte técnico do bot configurado com sucesso!")

# Comando /cadastrar para simular o registro de credenciais
@bot.message_handler(commands=['cadastrar'])
def cadastrar_api(message):
    bot.reply_to(
        message,
        "🔑 **Cadastro de Credenciais Shopee**\n\n"
        "Para gerar promoções com o seu link de afiliado real, envie seus dados ou acesse o Portal do Afiliado da Shopee.",
        parse_mode="Markdown"
    )

# Captura qualquer link enviado para transformar em oferta com botão
@bot.message_handler(func=lambda message: True)
def formatar_oferta(message):
    link_original = message.text.strip()
    
    if "http://" in link_original or "https://" in link_original:
        link_afiliado = f"{link_original}?uls_trackid=seu_codigo_aqui"
        
        texto_postagem = (
            "🔥 **ACHADINHO IMPERDÍVEL!** 🔥\n\n"
            "📦 Produto selecionado com excelente preço.\n"
            "🏃‍♂️ Corre que o estoque pode acabar rápido!\n\n"
            "👇 **Garanta o seu no link abaixo:**"
        )
        
        markup = InlineKeyboardMarkup()
        botao_comprar = InlineKeyboardButton("🛒 COMPRAR AGORA", url=link_afiliado)
        markup.add(botao_comprar)
        
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Digite `/menu` para abrir o painel de opções ou envie um link válido.")

print("Bot com menu interativo iniciado...")
bot.infinity_polling()
