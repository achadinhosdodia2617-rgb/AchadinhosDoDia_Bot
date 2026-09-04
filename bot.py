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
    return "Bot Casify Avançado rodando com máxima estabilidade!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Função de escape para evitar que caracteres especiais quebrem o Markdown do Telegram
def escapar_markdown(texto):
    if not texto:
        return ""
    caracteres = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in caracteres:
        texto = texto.replace(c, f"\\{c}")
    return texto

# Função para formatar o preço de forma limpa para o padrão brasileiro
def formatar_preco(preco_raw):
    try:
        # Se vier como float ou string numérica
        preco_float = float(preco_raw)
        return f"R$ {preco_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(preco_raw)

# Função universal para consultar a API com sistema de Tentativa Automática (Retry)
def consultar_shopee_api(keyword, tentativas=3):
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
    
    for tentativa_atual in range(tentativas):
        try:
            timestamp = int(time.time())
            factor = f"{SHOPEE_APP_ID}{timestamp}{payload_json}{SHOPEE_SECRET}"
            signature = hashlib.sha256(factor.encode('utf-8')).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'SHA256 Credential={SHOPEE_APP_ID},Timestamp={timestamp},Signature={signature}'
            }
            
            response = requests.post(url, headers=headers, data=payload_json, timeout=10)
            if response.status_code == 200:
                data = response.json()
                nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
                if nodes:
                    return nodes[0]
        except Exception as e:
            print(f"Tentativa {tentativa_atual + 1} falhou: {e}")
            time.sleep(1) # Aguarda 1 segundo antes de tentar novamente
            
    return None

# Gerador universal de frases de impacto dinâmicas
def gerar_frase_universal(keyword):
    kw = keyword.upper()
    return f"ACHADO IMPERDÍVEL: {kw} NO PRECIN TOP 🤌"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 *Casify - Painel Privado Avançado*\n\n"
        "Tudo pronto para operação em alta performance!\n\n"
        "💡 *Como usar:*\n"
        "• Digite qualquer produto (ex: _Fone Bluetooth_, _Smartwatch_, _Tênis_) para buscar com imagem, preço formatado e link de afiliado.\n"
        "• Ou envie o link direto da Shopee."
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Se enviou um link direto da Shopee
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link direto com rastreio de afiliado seguro...")
        
        link_afiliado = texto_usuario.split("?")[0] + "?uls_trackid=casify_track"
        
        texto_postagem = (
            "ACHADO IMPERDÍVEL NA SHOPEE 🔥\n\n"
            "✅ Oferta Selecionada com Desconto Exclusivo\n\n"
            "🔥 *OFERTA ESPECIAL LIBERADA* 🔥 no PIX\n\n"
            "✨ _Casify_"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        
    else:
        # Busca inteligente com retries automáticos
        bot.reply_to(message, f"🔍 Varrendo o catálogo da Shopee por '{texto_usuario}'...")
        
        produto = consultar_shopee_api(texto_usuario)
        
        if produto:
            nome_prod_raw = produto.get("productName", texto_usuario)
            preco_raw = produto.get("price", "Consulte")
            imagem_url = produto.get("imageUrl")
            link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            
            # Formatações seguras
            nome_prod = escapar_markdown(nome_prod_raw)
            preco_formatado = formatar_preco(preco_raw)
            frase_topo = gerar_frase_universal(texto_usuario)
            
            # Verifica se o produto tem indicações especiais no nome para incrementar o post
            tag_extra = ""
            if "frete grátis" in nome_prod_raw.lower():
                tag_extra = "🚚 *Frete Grátis Disponível*\n"
            
            # Montagem final da postagem profissional
            texto_postagem = (
                f"{frase_topo}\n\n"
                f"{tag_extra}"
                f"✅ {nome_prod}\n\n"
                f"🔥 *POR {preco_formatado}* 🔥 no PIX\n\n"
                "✨ _Casify_"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
            
            # Envia a foto com segurança
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
                f"⚠️ Não encontrei ofertas ativas para '{texto_usuario}' após algumas tentativas. "
                "💡 *Dica:* Tente usar termos mais curtos ou envie o link direto do produto."
            , parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    
    print("Bot Casify Avançado iniciado com sucesso!")
    bot.infinity_polling()
