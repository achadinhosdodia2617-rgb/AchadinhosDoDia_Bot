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
    return "Bot SetupDrop (Busca Ampla & Qualidade) rodando perfeitamente!"

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
        return f"{url_limpa}?uls_trackid=setupdrop_geek"
    except Exception as e:
        print(f"Erro ao expandir link: {e}")
        return url_curta

def processar_termo_setup_flexivel(texto):
    texto_limpo = texto.lower().strip()
    
    mapa_atalhos = {
        "mouse": "mouse gamer rgb",
        "teclado": "teclado mecanico gamer",
        "headset": "headset gamer",
        "fone": "fone gamer bluetooth",
        "cadeira": "cadeira gamer",
        "monitor": "monitor gamer",
        "mousepad": "mousepad grande gamer",
        "microfone": "microfone gamer rgb",
        "suporte": "suporte monitor",
        "controle": "controle gamer pc"
    }
    
    if texto_limpo in mapa_atalhos:
        return mapa_atalhos[texto_limpo]
        
    return texto_limpo

def validar_qualidade_produto(nome_produto):
    nome_upper = nome_produto.upper()
    termos_proibidos = ["GENÉRICO DESCARTAVEL", "REPLICA GROSSA"]
    for termo in termos_proibidos:
        if termo in nome_upper:
            return False
    return True

def consultar_shopee_avancado(keyword, min_price=None, max_price=None, sort_type=1, tentativas=3):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    termo_otimizado = processar_termo_setup_flexivel(keyword)
    
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
                    nodes_filtrados = [n for n in nodes if validar_qualidade_produto(n.get("productName", ""))]
                    if nodes_filtrados:
                        return nodes_filtrados
        except Exception as e:
            print(f"Tentativa {tentativa_atual + 1} falhou: {e}")
            time.sleep(1)
    return []

def gerar_gancho_setupdrop(nome_produto):
    nome_upper = nome_produto.upper()
    if any(p in nome_upper for p in ["TECLADO", "SWITCH"]):
        return "LEVEL UP NO SEU SETUP! TECLADO MECÂNICO MONSTRO ⌨️🔥"
    elif any(p in nome_upper for p in ["MOUSE", "MOUSEPAD"]):
        return "PRECISÃO ABSOLUTA PRA SUAS RANKEDs 🖱️⚡"
    elif any(p in nome_upper for p in ["HEADSET", "FONE", "MICROFONE"]):
        return "IMERSÃO TOTAL E ÁUDIO CRISTALINO NO JOGO 🎧🎮"
    elif any(p in nome_upper for p in ["CADEIRA", "SUPORTE"]):
        return "CONFORTO EXTREMO PARA MARATONAS DE JOGOS 💺👑"
    elif any(p in nome_upper for p in ["MONITOR", "LUZ", "LED", "RGB"]):
        return "DEIXE SEU SETUP COM VISUAL DE CYBERPUNK 💡✨"
    else:
        return "ACHADINHO GEEK DE ALTA QUALIDADE PARA O SEU SETUP 🚀"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⌨️ Periféricos", callback_data="cat_perifericos"),
        InlineKeyboardButton("🎧 Áudio & Headsets", callback_data="cat_audio")
    )
    markup.add(
        InlineKeyboardButton("💺 Cadeiras & Mesas", callback_data="cat_cadeiras"),
        InlineKeyboardButton("💡 Iluminação & RGB", callback_data="cat_iluminacao")
    )
    
    welcome_text = (
        "⚡ *SetupDrop - Gear & Setup Geek* ativo!\n\n"
        "Busca ampliada e flexível ativada! Envie o nome de qualquer equipamento, marca ou escolha uma categoria abaixo:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def callback_categorias(call):
    categoria = call.data.split("_")[1]
    termos_map = {
        "perifericos": "teclado mecanico mouse gamer",
        "audio": "headset gamer microfone",
        "cadeiras": "cadeira gamer escritorio",
        "iluminacao": "barra de luz rgb monitor"
    }
    keyword = termos_map.get(categoria, "setup gamer")
    bot.answer_callback_query(call.id, f"Buscando ofertas de {categoria}...")
    bot.send_message(call.message.chat.id, f"⚡ Garimpando os melhores itens de *{categoria.upper()}*...", parse_mode="Markdown")
    
    produtos = consultar_shopee_avancado(keyword, sort_type=1)
    processar_e_enviar_produtos(call.message.chat.id, produtos, keyword)

@bot.message_handler(commands=['fila'])
def ver_fila(message):
    if not FILA_RASCUNHOS:
        bot.reply_to(message, "📭 Fila de posts vazia.")
    else:
        bot.reply_to(message, f"📋 Você tem **{len(FILA_RASCUNHOS)}** itens na fila.", parse_mode="Markdown")

@bot.message_handler(commands=['limparfila'])
def limpar_fila(message):
    global FILA_RASCUNHOS
    FILA_RASCUNHOS = []
    bot.reply_to(message, "🗑️ Fila limpa com sucesso!")

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
            gancho_topo = gerar_gancho_setupdrop(nome_prod_raw)
            
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
            
            trecho_cupom = ""
            if tem_desconto_real or any(termo in nome_prod_raw.upper() for termo in ["CUPOM", "FRETE GRÁTIS", "PROMO"]):
                trecho_cupom = "🎟️ *Aplicar Cupom na Página!*\n\n"
            
            texto_postagem = (
                f"{gancho_topo}\n\n"
                f"✅ {nome_prod}\n\n"
                f"{bloco_preco}"
                f"{trecho_cupom}"
                f"🔗 {link_afiliado}\n\n"
                "SetupDrop • #SetupGamer #Geek"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 VER NA LOJA / COMPRAR", url=link_afiliado))
            
            if imagem_url:
                try:
                    bot.send_photo(chat_id, photo=imagem_url, caption=texto_postagem, reply_markup=markup, parse_mode="Markdown")
                except:
                    bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 100:
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 5:
                break
            time.sleep(0.4)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Produtos para '{termo_busca}' já foram enviados recentemente. Tente outro termo!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras-chave livres.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link...")
        link_afiliado = expandir_link_shopee(texto_usuario)
        texto_postagem = (
            "SETUPDROP • ACHADINHO DESTAQUE ⚡\n\n"
            "✅ Equipamento Selecionado\n\n"
            "🔥 GARANTA O SEU COM ESSE PREÇO 🔥\n\n"
            f"🔗 {link_afiliado}\n\n"
            "SetupDrop"
        )
        FILA_RASCUNHOS.append(texto_postagem)
        bot.send_message(message.chat.id, "📦 Adicionado à fila do SetupDrop!", parse_mode="Markdown")
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

        bot.reply_to(message, f"⚡ Buscando ofertas amplas para: *{termo_busca}*...", parse_mode="Markdown")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot SetupDrop (Busca Flexível) iniciado com sucesso!")
    bot.infinity_polling()
PRAR", url=link_afiliado))
            
            if imagem_url:
                try:
                    bot.send_photo(chat_id, photo=imagem_url, caption=texto_postagem, reply_markup=markup, parse_mode="Markdown")
                except:
                    bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, texto_postagem, reply_markup=markup, parse_mode="Markdown")
            
            HISTORICO_ENVIADOS.add(link_afiliado)
            if len(HISTORICO_ENVIADOS) > 100:  # Aumentado o histórico para suportar muito mais volume
                HISTORICO_ENVIADOS.pop()
                
            enviados_nesta_busca += 1
            if enviados_nesta_busca >= 5:  # Aumentado de 3 para 5 produtos por lote de busca
                break
            time.sleep(0.4)
            
        if enviados_nesta_busca == 0:
            bot.send_message(chat_id, f"⚠️ Produtos para '{termo_busca}' já foram enviados recentemente. Tente outro termo!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum resultado encontrado para '{termo_busca}'. Tente buscar com outras palavras-chave livres.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link...")
        link_afiliado = expandir_link_shopee(texto_usuario)
        texto_postagem = (
            "SETUPDROP • ACHADINHO DESTAQUE ⚡\n\n"
            "✅ Equipamento Selecionado\n\n"
            "🔥 GARANTA O SEU COM ESSE PREÇO 🔥\n\n"
            f"🔗 {link_afiliado}\n\n"
            "SetupDrop"
        )
        FILA_RASCUNHOS.append(texto_postagem)
        bot.send_message(message.chat.id, "📦 Adicionado à fila do SetupDrop!", parse_mode="Markdown")
    else:
        min_p, max_p = None, None  # Sem restrição de preço mínimo travado
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

        bot.reply_to(message, f"⚡ Buscando ofertas amplas para: *{termo_busca}*...", parse_mode="Markdown")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot SetupDrop (Busca Flexível) iniciado com sucesso!")
    bot.infinity_polling()
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
            
            trecho_cupom = ""
            if tem_desconto_real or any(termo in nome_prod_raw.upper() for termo in ["CUPOM", "FRETE GRÁTIS", "PROMO"]):
                trecho_cupom = "🎟️ *Aplicar Cupom na Página!*\n\n"
            
            texto_postagem = (
                f"{gancho_topo}\n\n"
                f"✅ {nome_prod}\n\n"
                f"{bloco_preco}"
                f"{trecho_cupom}"
                f"🔗 {link_afiliado}\n\n"
                "SetupDrop • #SetupGamer #Geek"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔗 VER NA LOJA / COMPRAR", url=link_afiliado))
            
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
            bot.send_message(chat_id, f"⚠️ Produtos para '{termo_busca}' já foram enviados recentemente. Tente outro item gamer!", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Nenhum item de alta qualidade encontrado para '{termo_busca}'. Tente buscar outro equipamento do setup.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link de produto gamer...")
        link_afiliado = expandir_link_shopee(texto_usuario)
        texto_postagem = (
            "SETUPDROP • ACHADINHO DESTAQUE ⚡\n\n"
            "✅ Equipamento Selecionado\n\n"
            "🔥 GARANTA O SEU COM ESSE PREÇO 🔥\n\n"
            f"🔗 {link_afiliado}\n\n"
            "SetupDrop"
        )
        FILA_RASCUNHOS.append(texto_postagem)
        bot.send_message(message.chat.id, "📦 Adicionado à fila do SetupDrop!", parse_mode="Markdown")
    else:
        min_p, max_p = 30.0, None  # Preço mínimo de segurança
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

        bot.reply_to(message, f"⚡ Garimpando hardware e acessórios de alta qualidade...")
        produtos = consultar_shopee_avancado(termo_busca, min_price=min_p, max_price=max_p, sort_type=1)
        processar_e_enviar_produtos(message.chat.id, produtos, termo_busca)

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot SetupDrop (Geek & Gamer) iniciado com sucesso!")
    bot.infinity_polling()
in nome_prod_raw.upper() for termo in ["CUPOM", "FRETE GRÁTIS", "FRETE GRATIS", "OFERTA", "PROMO"]):
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
