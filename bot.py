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

# Servidor web simples para manter o Render ativo
app = Flask('')

@app.route('/')
def home():
    return "Bot Casify Universal (Afiliado Ativo) rodando com sucesso!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Função universal para consultar qualquer produto na API de Afiliados da Shopee
def consultar_shopee_api(keyword):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    # Consulta estruturada para extrair dados precisos e link de afiliado oficial
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

# Gerador universal de frases de impacto adaptadas para QUALQUER produto buscado
def gerar_frase_universal(keyword):
    kw = keyword.upper()
    return f"ACHADO IMPERDÍVEL: {kw} NO PRECIN TOP 🤌"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 **Casify - Painel Privado (Universal)**\n\n"
        "Tudo pronto para você e sua esposa operarem!\n\n"
        "💡 **Como usar:**\n"
        "• Digite **qualquer produto** (ex: *Panela Elétrica*, *Fone Bluetooth*, *Smartwatch*, *Tênis Nike*) e o bot vai buscar a imagem, o preço real e o **seu link de afiliado** automaticamente.\n"
        "• Ou envie o **link direto** da Shopee.\n\n"
        "✨ *Bora garimpar e faturar comissões!*"
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Se enviou um link direto da Shopee
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link direto com rastreio de afiliado...")
        
        # Garante o rastreio caso venha limpo
        link_afiliado = texto_usuario.split("?")[0] + "?uls_trackid=casify_track"
        
        texto_postagem = (
            "ACHADO IMPERDÍVEL NA SHOPEE 🔥\n\n"
            "✅ Oferta Selecionada com Desconto Exclusivo\n\n"
            "🔥 **OFERTA ESPECIAL LIBERADA** 🔥 no PIX\n\n"
            "✨ *Casify*"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        
    else:
        # Busca universal por qualquer palavra-chave informada
        bot.reply_to(message, f"🔍 Varrendo o catálogo da Shopee por '{texto_usuario}'...")
        
        produto = consultar_shopee_api(texto_usuario)
        
        if produto:
            nome_prod = produto.get("productName", texto_usuario)
            preco = produto.get("price", "Consulte")
            imagem_url = produto.get("imageUrl")
            
            # LINK DE AFILIADO OFICIAL FORNECIDO PELA API DA SHOPEE
            link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            
            # Frase adaptada automaticamente para o produto buscado
            frase_topo = gerar_frase_universal(texto_usuario)
            
            # Montagem da postagem no padrão profissional (igual aos prints)
            texto_postagem = (
                f"{frase_topo}\n\n"
                f"✅ {nome_prod}\n\n"
                f"🔥 **POR R$ {preco}** 🔥 no PIX\n\n"
                "✨ *Casify*"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
            
            # Envia a foto oficial do produto junto com a legenda formatada e o link com comissão
            if imagem_url:
                try:
                    bot.send_photo(
                        message.chat.id, 
                        photo=imagem_url, 
                        caption=texto_postagem, 
                        reply_markup=markup, 
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
                
        else:
            bot.send_message(
                message.chat.id, 
                f"⚠️ Não encontrei ofertas ativas para '{texto_usuario}'. "
                "💡 **Dica:** Tente usar termos mais comerciais ou o link direto do produto."
            , parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot Casify Universal iniciado com sucesso!")
    bot.infinity_polling()
