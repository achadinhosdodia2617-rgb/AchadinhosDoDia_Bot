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

# Histórico anti-repetição otimizado
HISTORICO_ENVIADOS = set()

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

def processar_termo_inteligente(texto):
    texto_limpo = texto.lower().strip()
    
    expansoes = {
        "copo": "copo termico inox Stanley",
        "copos": "copo termico inox Stanley",
        "prato": "jogo de pratos rasos fundo",
        "pratos": "jogo de pratos rasos fundo",
        "xícara": "xicara de cha com pires",
        "xicara": "xicara de cha com pires",
        "caneca": "caneca personalizada criativa",
        "pano": "pano de prato kit estampado",
        "papel": "papel toalha rolo grande",
        "mesa": "mesa posta jogo americano",
        "mesas": "mesa de centro industrial",
        "caneta": "caneta touch universal stylus",
        "conjunto": "conjunto feminino duna short saia"
    }
    
    if texto_limpo in expansoes:
        return expansoes[texto_limpo]
        
    stopwords = {"de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi", "ao", "ele", "das", "às", "seu", "sua", "ou", "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "quem", "nas", "esse", "num", "usado", "quero", "achar", "encontrar"}
    
    palavras = texto_limpo.split()
    palavras_filtradas = [p for p in palavras if p not in stopwords]
    
    if palavras_filtradas:
        return " ".join(palavras_filtradas)
    return texto_limpo

def consultar_shopee_avancado(keyword, min_price=None, max_price=None, sort_type=1, tentativas=3):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    termo_otimizado = processar_termo_inteligente(keyword)
    
    args = [f'keyword: "{termo_otimizado}"', f'limit: 50', f'sortType: {sort_type}']
    if min_price is not None:
        args.append(f'minPrice: {min_price}')
    if max_price is not None:
        args.append(f'maxPrice: {max_price}')
        
    args_str = ", ".join(args)

    query_str = f"""
    {{
      productOfferV2({args_str}) {{
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
        return "O QUERIDINHO DO MOMENTO QUE ESGOTA RÁPIDO ✨"
    elif any(p in nome_upper for p in ["CADEIRA", "ESCRITORIO", "GAMER"]):
        return "CONFORTO E CUSTO-BENEFÍCIO EXCEPCIONAL"
    elif any(p in nome_upper for p in ["CONJUNTO", "VESTIDO", "CROPPED", "SAIA"]):
        return "LOOK PERFEITO PRA VOCÊ ARRASAR EM QUALQUER LUGAR 😍"
    elif any(p in nome_upper for p in ["TOALHA", "KIT", "JOGO", "PANELA", "COPO", "PRATO", "CANECA", "CANETA"]):
        return "ACHADINHO QUE VOCÊ PRECISA TER EM CASA 🤌"
    else:
        return "ACHADINHO IMPERDÍVEL LIBERADO AGORA 🚀"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📱 Eletrônicos", callback_data="cat_eletronicos"),
        InlineKeyboardButton("👗 Moda & Look", callback_data="cat_moda")
    )
    markup.add(
        InlineKeyboardButton("🏠 Casa & Cozinha", callback_data="cat_casa"),
        InlineKeyboardButton("✨ Mais Vendidos", callback_data="cat_populares")
    )
    
    welcome_text = (
        "🤖 *Casify Pixel-Perfect* ativo!\n\n"
        "Envie o nome de qualquer produto, frases naturais, links da Shopee ou escolha uma das categorias abaixo:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def callback_categorias(call):
    categoria = call.data.split("_")[1]
    termos_map = {
        "eletronicos": "fone bluetooth smartwatch",
        "moda": "vestido feminino cropped",
        "casa": "jogo de panelas organizer",
        "populares": "achadinhos virais shopee"
    }
    keyword = termos_map.get(categoria, "achados shopee")
    bot.answer_callback_query(call.id, f"Buscando ofertas de {categoria}...")
    bot.send_message(call.message.chat.id, f"🔍 Garimpando os melhores itens de *{categoria.upper()}*...", parse_mode="Markdown")
    
    produtos = consultar_shopee_avancado(keyword, sort_type=1)
    processar_e_enviar_produtos(call.message.chat.id, produtos, keyword)

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

def processar_e_enviar_produtos(chat_id, produtos, termo_busca):
    global HISTORICO_ENVIADOS
    enviados_nesta_busca = 0
    
    if produtos:
        for produto in produtos:
            link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
            
            if link_afiliado in HISTORICO_ENVIADOS:
                continue
                
            nome_prod_raw = produto.get("productName", termo_busca)
            preco_raw = produto.get("price", "0")
            preco_max_raw = produto.get("priceMax")
            imagem_url = produto.get("imageUrl")
            
            nome_prod = escapar_markdown(nome_prod_raw)
            preco_formatado = formatar_preco(preco_raw)
            gancho_topo = gerar_gancho_promosam(nome_prod_raw)
            
            # Geração limpa do parcelamento sem bugs de duplicação
            trecho_parcelamento = ""
            try:
                p_val = float(preco_raw)
                if p_val > 40:
                    parcelas = 12 if p_val > 200 else 6
                    v_parcela = p_val / parcelas
                    trecho_parcelamento = f" ou em até {parcelas}x de {formatar_preco(v_parcela)}"
            except:
                pass
            
            bloco_preco = f"🔥 POR {preco_formatado} no Pix{trecho_parcelamento} 🔥\n\n"
            tem_desconto_real = False
            try:
                if preco_max_raw and float(preco_max_raw) > float(preco_raw):
                    p_max = float(preco_max_raw)
                    p_min = float(preco_raw)
                    economia = int(((p_max - p_min) / p_max) * 100)
                    de_formatado = formatar_preco(preco_max_raw)
                    bloco_preco = (
                        f"DE ~~{de_formatado}~~\n"
                        f"🔥 POR {preco_formatado} no Pix ({economia}% OFF){trecho_parcelamento} 🔥\n\n"
                    )
                    tem_desconto_real = True
            except:
                pass
            
            # Linha transparente de cupom baseada estritamente em regras reais (sem strings falsas)
            trecho_cupom = ""
            if tem_desconto_real or any(termo in nome_prod_raw.upper() for termo in ["CUPOM", "FRETE GRÁTIS", "FRETE GRATIS", "OFERTA", "PROMO"]):
                trecho_cupom = "🎟️ *Aplicar Cupom na Página!*\n\n"
            
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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 50:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 3:
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos retornados para '{termo_busca}' já estão no histórico recente. Tente buscar novamente!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando um lote amplo de ofertas...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Versão Definitiva) iniciado com sucesso!")
    bot.infinity_polling()
) for termo in ["CUPOM", "FRETE GRÁTIS", "FRETE GRATIS", "OFERTA", "PROMO"]):
                trecho_cupom = "🎟️ *Aplicar Cupom na Página!*\n\n"
            
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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 50:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 3:
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos retornados para '{termo_busca}' já estão no histórico recente. Tente buscar novamente!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando um lote amplo de ofertas...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Pix & Preço Perfeito) iniciado com sucesso!")
    bot.infinity_polling()
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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 50:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 3:
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos retornados para '{termo_busca}' já estão no histórico recente. Tente buscar novamente!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando um lote amplo de ofertas...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Com Aviso de Cupom Real) iniciado com sucesso!")
    bot.infinity_polling()
IS" in nome_upper or "FRETE GRATIS" in nome_upper:
                trecho_cupom = "🚚 *Produto com benefício de Frete Grátis!*\n\n"
            elif "CUPOM" in nome_upper:
                trecho_cupom = "🎟️ *Verifique cupons disponíveis na página do produto*\n\n"
            
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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 150:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 2:  # Limita a 2 produtos únicos por busca
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos encontrados para '{termo_busca}' já foram enviados recentemente. Tente outro termo!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando com inteligência artificial...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Sem Cupons Fictícios) iniciado com sucesso!")
    bot.infinity_polling()
IS" in nome_upper or "FRETE GRATIS" in nome_upper:
                trecho_cupom = "🚚 *Produto com benefício de Frete Grátis!*\n\n"
            elif "CUPOM" in nome_upper:
                trecho_cupom = "🎟️ *Verifique cupons disponíveis na página do produto*\n\n"
            
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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 150:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 2:  # Limita a 2 produtos únicos por busca
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos encontrados para '{termo_busca}' já foram enviados recentemente. Tente outro termo!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando com inteligência artificial...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Sem Cupons Fictícios) iniciado com sucesso!")
    bot.infinity_polling()

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
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 150:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 2:  # Limita a 2 produtos únicos por busca
                break
            time.sleep(0.5)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Todos os produtos encontrados para '{termo_busca}' já foram enviados recentemente. Tente outro termo!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras.", parse_mode="Markdown")

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
        min_p, max_p = None, None
        termo_busca = texto_usuario
        
        if "|" in texto_usuario:
            partes = [p.strip() for p in texto_usuario.split("|")]
            termo_busca = partes[0]
            for parte in partes[1:]:
                if parte.lower().startswith("min:"):
                    try:
                        min_p = float(parte.split(":")[1].strip())
                    except:
                        pass
                elif parte.lower().startswith("max:"):
                    try:
                        max_p = float(parte.split(":")[1].strip())
                    except:
                        pass

        bot.reply_to(message, f"🔍 Garimpando com inteligência artificial...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 (Versão Definitiva) iniciado com sucesso!")
    bot.infinity_polling()
