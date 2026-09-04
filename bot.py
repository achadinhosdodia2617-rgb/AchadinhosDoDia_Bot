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
    return "Bot Casify Master (Ads & Pix Inteligente) rodando com sucesso!"

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

# Função para formatar o preço no padrão brasileiro
def formatar_preco(preco_raw):
    try:
        preco_float = float(preco_raw)
        return f"R$ {preco_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(preco_raw)

# Função para expandir links curtos da Shopee (s.shopee.com.br) e extrair a URL limpa
def expandir_link_shopee(url_curta):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url_curta, allow_redirects=True, headers=headers, timeout=5)
        url_final = response.url
        url_limpa = url_final.split("?")[0]
        return f"{url_limpa}?uls_trackid=casify_track"
    except Exception as e:
        print(f"Erro ao expandir link: {e}")
        return url_curta

# Consulta à API com sistema de Tentativa Automática (Retry) e extração de comissão
def consultar_shopee_api(keyword, tentativas=3):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    # Solicitamos também o campo commissionRate para identificar campanhas e anúncios fortes
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
            time.sleep(1)
            
    return None

# Gerador universal de frases de impacto dinâmicas
def gerar_frase_universal(keyword):
    kw = keyword.upper()
    return f"ACHADO IMPERDÍVEL: {kw} NO PRECIN TOP 🤌"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 *Casify - Painel Master Completo*\n\n"
        "Tudo pronto para operação em alta performance!\n\n"
        "💡 *Como usar:*\n"
        "• Digite qualquer produto para buscar com imagem, cálculo de desconto, destaque Pix e identificação de campanhas/Ads.\n"
        "• Ou envie o link direto / encurtado da Shopee."
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Se enviou um link (curto ou longo da Shopee)
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Analisando link, ativando rastreio e verificando status de campanha...")
        
        link_afiliado = expandir_link_shopee(texto_usuario)
        
        texto_postagem = (
            "ACHADO IMPERDÍVEL NA SHOPEE 🔥\n\n"
            "⭐ *PRODUTO EM DESTAQUE / PATROCINADO* ⭐\n\n"
            "🔥 *OFERTA ESPECIAL COM DESCONTO NO PIX* 🔥\n\n"
            "✨ _Casify_"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 CLIQUE PARA ABRIR O LINK", url=link_afiliado))
        bot.send_message(message.chat.id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
        
    else:
        # Busca inteligente por palavra-chave
        bot.reply_to(message, f"🔍 Varrendo o catálogo da Shopee por '{texto_usuario}'...")
        
        produto = consultar_shopee_api(texto_usuario)
        
        if produto:
            nome_prod_raw = produto.get("productName", texto_usuario)
            preco_raw = produto.get("price", "Consulte")
            preco_max_raw = produto.get("priceMax")
            imagem_url = produto.get("imageUrl")
            link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            comissao = produto.get("commissionRate", 0)
            
            # Formatações seguras
            nome_prod = escapar_markdown(nome_prod_raw)
            preco_formatado = formatar_preco(preco_raw)
            frase_topo = gerar_frase_universal(texto_usuario)
            
            # Identificação inteligente de Ads / Campanhas Fortes baseado na comissão alta retornada pela API
            tag_ads = ""
            try:
                # Se a comissão for expressiva, indica que o produto está recebendo forte investimento/patrocínio
                if comissao and float(comissao) > 5.0: 
                    tag_ads = "⭐ *PRODUTO EM DESTAQUE / PATROCINADO* ⭐\n"
            except:
                pass
            
            # Bloco inteligente de Preço, Desconto e Vantagem no PIX
            bloco_preco = ""
            try:
                if preco_max_raw and float(preco_max_raw) > float(preco_raw):
                    p_max = float(preco_max_raw)
                    p_min = float(preco_raw)
                    economia = int(((p_max - p_min) / p_max) * 100)
                    de_formatado = formatar_preco(preco_max_raw)
                    
                    preco_pix = p_min * 0.95
                    preco_pix_formatado = formatar_preco(preco_pix)
                    
                    bloco_preco = (
                        f"DE ~~{de_formatado}~~\n"
                        f"🔥 *POR {preco_formatado}* ({economia}% OFF)\n"
                        f"⚡ *MENOR PREÇO NO PIX:* *{preco_pix_formatado}* 💸\n\n"
                    )
                else:
                    bloco_preco = (
                        f"🔥 *POR {preco_formatado}*\n"
                        f"⚡ *MENOR PREÇO NO PIX* 💸\n\n"
                    )
            except:
                bloco_preco = f"🔥 *POR {preco_formatado}* no PIX 🔥\n\n"
            
            # Tags extras baseadas no nome (como frete grátis)
            tag_extra = ""
            if "frete grátis" in nome_prod_raw.lower():
                tag_extra = "🚚 *Frete Grátis Disponível*\n"
            
            # Montagem final da postagem profissional
            texto_postagem = (
                f"{frase_topo}\n\n"
                f"{tag_ads}"
                f"{tag_extra}"
                f"✅ {nome_prod}\n\n"
                f"{bloco_preco}"
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
    
    print("Bot Casify Master (Com Ads & Pix) iniciado com sucesso!")
    bot.infinity_polling()
