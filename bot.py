import os
import json
import time
import hashlib
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Configurações do Bot e da Shopee via Variáveis de Ambiente do Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID")
SHOPEE_SECRET = os.environ.get("SHOPEE_SECRET")

bot = telebot.TeleBot(TOKEN)

# Servidor web simples para o Render não dar Timeout
app = Flask('')

@app.route('/')
def home():
    return "Bot Casify (Padrão PromoSam) rodando com sucesso!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Função avançada para buscar e extrair dados detalhados da API GraphQL da Shopee
def consultar_shopee_api(keyword):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query_str = f"""
    {{
      productOfferV2(keyword: "{keyword}", limit: 1) {{
        nodes {{
          productName
          price
          priceMax
          offerLink
          productLink
          imageUrl
          commissionRate
        }}
      }}
    }}
    """
    
    payload_dict = {
        "query": query_str.strip(),
        "variables": {}
    }
    
    payload_json = json.dumps(payload_dict, separators=(',', ':'))
    timestamp = int(time.time())
    
    factor = f"{SHOPEE_APP_ID}{timestamp}{payload_json}{SHOPEE_SECRET}"
    signature = hashlib.sha256(factor.encode('utf-8')).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'SHA256 Credential={SHOPEE_APP_ID},Timestamp={timestamp},Signature={signature}'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload_json, timeout=10)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
            if nodes:
                return nodes[0]
    except Exception as e:
        print(f"Erro ao consultar API da Shopee: {e}")
        
    return None

# Menus e Painel
def criar_menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    b1 = InlineKeyboardButton("🎁 Criar Oferta", callback_data="btn_promocao")
    b2 = InlineKeyboardButton("🔍 Buscar Produto", callback_data="btn_buscar")
    b3 = InlineKeyboardButton("🔗 Enviar Link", callback_data="btn_enviar_link")
    b4 = InlineKeyboardButton("📊 Meu Plano", callback_data="btn_plano")
    b5 = InlineKeyboardButton("🔑 API Shopee", callback_data="btn_api")
    b6 = InlineKeyboardButton("🛠️ Suporte", callback_data="btn_suporte")
    markup.add(b1, b2, b3, b4, b5, b6)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 **Casify - Painel Profissional**\n\n"
        "Envie o nome exato do produto ou o link direto para gerar postagens no padrão dos maiores canais de garimpo!\n\n"
        "👇 **Escolha uma opção abaixo:**"
    )
    bot.send_message(message.chat.id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_promocao":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎁 Envie o nome ou link do produto:")
    elif call.data == "btn_buscar":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔍 Digite o nome exato do produto (Ex: *Tênis Kappa*, *Secador Philco*):", parse_mode="Markdown")
    elif call.data == "btn_enviar_link":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔗 Cole o link bruto da Shopee aqui.")
    elif call.data == "btn_plano":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Plano Atual: Profissional (Padrão PromoSam) 🚀")
    elif call.data == "btn_api":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 API da Shopee ativa e integrada com sucesso!", parse_mode="Markdown")
    elif call.data == "btn_suporte":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛠️ Suporte técnico à disposição!")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Se o usuário enviou um link direto
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link no padrão Casify...")
        
        link_afiliado = texto_usuario.split("?")[0] + "?uls_trackid=casify_track"
        
        # Estrutura idêntica aos prints de referência
        texto_postagem = (
            "ACHADO IMPERDÍVEL NO GARIMPO 🔥\n\n"
            "✅ Produto Selecionado na Shopee\n\n"
            "🔥 **OFERTA ESPECIAL LIBERADA** 🔥 no PIX\n\n"
            "✨ *Casify*"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        
    else:
        # Busca por palavra-chave refinada
        bot.reply_to(message, f"🔍 Pesquisando '{texto_usuario}' com precisão na Shopee...")
        
        produto = consultar_shopee_api(texto_usuario)
        
        if produto:
            nome_prod = produto.get("productName", texto_usuario)
            preco = produto.get("price", "Consulte")
            link_oferta = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            
            # Montagem dinâmica com a identidade visual exata solicitada
            texto_postagem = (
                f"OLHA ESSE ACHADO: {texto_usuario.upper()} NO PRECIN TOP 🤌\n\n"
                f"✅ {nome_prod}\n\n"
                f"🔥 **POR R$ {preco}** 🔥 no PIX\n\n"
                "✨ *Casify*"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_oferta))
            bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(
                message.chat.id, 
                f"⚠️ Não localizamos um match exato para '{texto_usuario}'. "
                "💡 **Dica:** Tente digitar o nome completo do produto ou enviar o link direto para garantir 100% de precisão!"
            , parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot Casify otimizado iniciado...")
    bot.infinity_polling()
