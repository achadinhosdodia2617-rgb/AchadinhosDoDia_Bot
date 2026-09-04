import os
import json
import time
import hashlib
import hmac
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# Configurações do Bot e da Shopee puxadas direto das Variáveis de Ambiente do Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID")
SHOPEE_SECRET = os.environ.get("SHOPEE_SECRET")

bot = telebot.TeleBot(TOKEN)

# Servidor web simples para o Render não dar Timeout
app = Flask('')

@app.route('/')
def home():
    return "Bot Casify (com API Shopee Oficial) rodando com sucesso!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Função para consultar a API GraphQL de Afiliados da Shopee com assinatura HMAC-SHA256
def consultar_shopee_api(keyword):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    # Query GraphQL estruturada para buscar ofertas de produtos por palavra-chave
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
    
    # Assinatura de segurança exigida pela API da Shopee: AppID + timestamp + payload + secret
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

# Menus e Funções do Bot
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
        "🤖 **Casify - Painel Oficial**\n\n"
        "Envie o nome de um produto para buscar na Shopee via API ou mande um link direto para gerar sua oferta!\n\n"
        "👇 **Escolha uma opção abaixo:**"
    )
    bot.send_message(message.chat.id, texto, reply_markup=criar_menu_principal(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_promocao":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎁 Envie o nome ou link do produto que deseja transformar em oferta:")
    elif call.data == "btn_buscar":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔍 Digite o que deseja buscar (Ex: *Liquidificador*, *Mixer*):", parse_mode="Markdown")
    elif call.data == "btn_enviar_link":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔗 Cole o seu link da Shopee aqui.")
    elif call.data == "btn_plano":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📊 Plano Atual: Profissional (API Shopee Conectada) 🚀")
    elif call.data == "btn_api":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔑 API da Shopee ativa e configurada com segurança no ambiente!", parse_mode="Markdown")
    elif call.data == "btn_suporte":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🛠️ Suporte técnico à disposição!")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Se o usuário enviou um link direto
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link...")
        link_afiliado = f"{texto_usuario}?uls_trackid=casify_track"
        
        texto_postagem = (
            "PRECISAVA DESSA NO GARIMPO 🤌\n\n"
            "✅ Produto Shopee\n\n"
            "🔥 **Oferta imperdível no PIX** 🔥\n\n"
            "✨ *Casify*"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        
    else:
        # Se o usuário digitou texto, busca na API de afiliados da Shopee
        bot.reply_to(message, f"🔍 Buscando '{texto_usuario}' na API da Shopee...")
        
        produto = consultar_shopee_api(texto_usuario)
        
        if produto:
            nome_prod = produto.get("productName", texto_usuario)
            preco = produto.get("price", "Consulte")
            link_oferta = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            
            texto_postagem = (
                "PRECISAVA DESSA NO GARIMPO 🤌\n\n"
                f"✅ {nome_prod}\n\n"
                f"🔥 **POR R$ {preco}** 🔥 no PIX\n\n"
                "✨ *Casify*"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_oferta))
            bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"⚠️ Não encontramos resultados diretos para '{texto_usuario}' via API. Tente enviar um link direto da Shopee.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot Casify com API Shopee iniciado...")
    bot.infinity_polling()
