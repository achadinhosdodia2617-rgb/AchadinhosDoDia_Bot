import os
import json
import time
import hashlib
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID")
SHOPEE_SECRET = os.environ.get("SHOPEE_SECRET")

bot = telebot.TeleBot(TOKEN)
FILA_RASCUNHOS = []

app = Flask('')

@app.route('/')
def home():
    return "Bot Casify Pixel-Perfect PromoSam rodando!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def escapar_markdown(texto):
    if not texto:
        return ""
    caracteres = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in caracteres:
        texto = texto.replace(c, f"\\{c}")
    return texto

def formatar_preco(preco_raw):
    try:
        preco_float = float(preco_raw)
        return f"R$ {preco_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(preco_raw)

def expandir_link_shopee(url_curta):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url_curta, allow_redirects=True, headers=headers, timeout=5)
        url_final = response.url
        url_limpa = url_final.split("?")[0]
        return f"{url_limpa}?uls_trackid=casify_perfect"
    except Exception as e:
        print(f"Erro ao expandir link: {e}")
        return url_curta

def consultar_shopee_api_multipla(keyword, tentativas=3):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    query_str = f"""
    {{
      productOfferV2(keyword: "{keyword}", limit: 3) {{
        nodes {{
          productName
          price
          priceMax
          offerLink
          productLink
          imageUrl
        }}
      }}
    }}
    """
    payload_dict = {"query": query_str.strip(), "variables": {}}
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
                    return nodes
        except Exception as e:
            print(f"Tentativa {tentativa_atual + 1} falhou: {e}")
            time.sleep(1)
    return []

def gerar_gancho_promosam(nome_produto):
    nome_upper = nome_produto.upper()
    if any(p in nome_upper for p in ["TÊNIS", "TENIS", "SAPATO", "SANDÁLIA", "CHINELO", "CHUTEIRA"]):
        return "OS DA MINHA COLEÇÃO ESTÃO COM INVEJA DESSA"
    elif any(p in nome_upper for p in ["FONE", "BLUETOOTH", "HEADSET", "SMARTWATCH", "CELULAR"]):
        return "TECNOLOGIA DE PONTA COM PREÇO ABSURDO 🔥"
    elif any(p in nome_upper for p in ["SECADOR", "ESCOVA", "CHAPINHA", "PERFUME"]):
        return "O QUERIDINHO DO MOMENTO QUE ESGOTÁVEL RÁPIDO ✨"
    elif any(p in nome_upper for p in ["CADEIRA", "ESCRITORIO", "GAMER"]):
        return "CONFORTO E CUSTOBENEFÍCIO EXCEPCIONAL"
    elif any(p in nome_upper for p in ["TOALHA", "KIT", "JOGO", "PANELA"]):
        return "SUAS COISAS MAIS FINAS QUE FOLHA DE PAPEL 🤌"
    else:
        return "ACHADINHO IMPERDÍVEL LIBERADO AGORA 🚀"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🤖 *Casify Pixel-Perfect* ativo e sincronizado com o padrão PromoSam!", parse_mode="Markdown")

@bot.message_handler(commands=['fila'])
def ver_fila(message):
    if not FILA_RASCUNHOS:
        bot.reply_to(message, "📭 Fila vazia.")
    else:
        bot.reply_to(message, f"📋 Você tem **{len(FILA_RASCUNHOS)}** itens na fila.", parse_mode="Markdown")

@bot.message_handler(commands=['limparfila'])
def limpar_fila(message):
    global FILA_RASCUNHOS
    FILA_RASCUNHOS = []
    bot.reply_to(message, "🗑️ Fila limpa!")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link...")
        link_afiliado = expandir_link_shopee(texto_usuario)
        texto_postagem = (
            "ACHADINHO ESPECIAL DA SHOPEE 🔥\n\n"
            "✅ Produto Selecionado\n\n"
            "🔥 POR APENAS UM PREÇO INCRÍVEL 🔥\n\n"
            f"🔗 {link_afiliado}\n\n"
            "anúncio"
        )
        FILA_RASCUNHOS.append(texto_postagem)
        bot.send_message(message.chat.id, "📦 Adicionado à fila!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "🔍 Garimpando no padrão exato...")
        produtos = consultar_shopee_api_multipla(texto_usuario)
        
        if produtos:
            chat_id = message.chat.id
            for produto in produtos:
                nome_prod_raw = produto.get("productName", texto_usuario)
                preco_raw = produto.get("price", "0")
                preco_max_raw = produto.get("priceMax")
                imagem_url = produto.get("imageUrl")
                link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
                
                nome_prod = escapar_markdown(nome_prod_raw)
                preco_formatado = formatar_preco(preco_raw)
                gancho_topo = gerar_gancho_promosam(nome_prod_raw)
                
                # Formatação idêntica aos prints (De / Por / Desconto / Parcelamento)
                trecho_parcelamento = ""
                try:
                    p_val = float(preco_raw)
                    if p_val > 80:
                        parcelas = 12 if p_val > 250 else 6
                        v_parcela = p_val / parcelas
                        trecho_parcelamento = f" em até {parcelas}x R$ {formatar_preco(v_parcela)}"
                except:
                    pass
                
                bloco_preco = f"🔥 POR {preco_formatado} 🔥{trecho_parcelamento}\n\n"
                try:
                    if preco_max_raw and float(preco_max_raw) > float(preco_raw):
                        p_max = float(preco_max_raw)
                        p_min = float(preco_raw)
                        economia = int(((p_max - p_min) / p_max) * 100)
                        de_formatado = formatar_preco(preco_max_raw)
                        bloco_preco = (
                            f"DE ~~{de_formatado}~~\n"
                            f"🔥 POR {preco_formatado} 🔥 ({economia}% OFF){trecho_parcelamento}\n\n"
                        )
                except:
                    pass
                
                # Linha de cupom estruturada idêntica aos prints com o ícone 🎟️
                trecho_cupom = "🎟️ Cupom: SUPERDESCONTO\n\n"
                
                # Montagem final exatamente como nos prints do PromoSam
                texto_postagem = (
                    f"{gancho_topo}\n\n"
                    f"✅ {nome_prod}\n\n"
                    f"{bloco_preco}"
                    f"{trecho_cupom}"
                    f"🔗 {link_afiliado}\n\n"
                    "anúncio"
                )
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🔗 ABRIR LINK DA OFERTA", url=link_afiliado))
                
                if imagem_url:
                    try:
                        bot.send_photo(chat_id, photo=imagem_url, caption=texto_postagem, reply_markup=markup, parse_mode="Markdown")
                    except:
                        bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
                
                time.sleep(0.5)
        else:
            bot.send_message(message.chat.id, f"⚠️ Nenhum produto encontrado para '{texto_usuario}'.", parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.infinity_polling()
             if imagem_url:
                    try:
                        bot.send_photo(chat_id, photo=imagem_url, caption=texto_postagem, reply_markup=markup, parse_mode="Markdown")
                    except:
                        bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
                
                time.sleep(0.5)
        else:
            bot.send_message(message.chat.id, f"⚠️ Nenhum resultado encontrado para '{texto_usuario}'. Tente buscar com outras palavras.", parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 iniciado com sucesso!")
    bot.infinity_polling()
