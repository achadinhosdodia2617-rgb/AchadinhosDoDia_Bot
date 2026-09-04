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

# Fila de rascunhos para o casal
FILA_RASCUNHOS = []

# Servidor web simples para manter o Render ativo
app = Flask('')

@app.route('/')
def home():
    return "Bot Casify Master 3.0 rodando com sucesso!"

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

# Função para expandir links curtos da Shopee e adicionar rastreio
def expandir_link_shopee(url_curta):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.head(url_curta, allow_redirects=True, headers=headers, timeout=5)
        url_final = response.url
        url_limpa = url_final.split("?")[0]
        return f"{url_limpa}?uls_trackid=casify_master_track"
    except Exception as e:
        print(f"Erro ao expandir link: {e}")
        return url_curta

# Consulta à API com tratamento avançado de falhas e ordenação inteligente
def consultar_shopee_api_multipla(keyword, tentativas=3):
    url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    query_str = f"""
    {{
      productOfferV2(keyword: "{keyword}", limit: 5) {{
        nodes {{
          productName
          price
          priceMax
          offerLink
          productLink
          imageUrl
          commissionRate
          sales
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
                    # Ordena inteligentemente por comissão ou relevância se disponível
                    return nodes[:3] # Retorna os 3 melhores
        except Exception as e:
            print(f"Tentativa {tentativa_atual + 1} falhou: {e}")
            time.sleep(1.5)
            
    return []

# Gerador avançado de ganchos comerciais por categoria
def gerar_gancho_promosam(nome_produto):
    nome_upper = nome_produto.upper()
    
    if any(p in nome_upper for p in ["TÊNIS", "TENIS", "SAPATO", "SANDÁLIA", "CHINELO", "CHUTEIRA", "SCARPIN", "BOTA"]):
        return "ACHADINHO DE RESPEITO PARA OS PÉS 👟"
    elif any(p in nome_upper for p in ["FONE", "BLUETOOTH", "HEADSET", "SMARTWATCH", "CELULAR", "CARREGADOR", "CAIXA DE SOM", "CABO", "SUPORTE"]):
        return "TECNOLOGIA COM PREÇO DE REVENDA 🔥"
    elif any(p in nome_upper for p in ["SECADOR", "ESCOVA", "CHAPINHA", "MODELADOR", "MAQUIAGEM", "PERFUME", "CREME", "SKINCARE", "PRANCHA"]):
        return "O QUERIDINHO DOS SALÕES E DOS CUIDADOS DIÁRIOS ✨"
    elif any(p in nome_upper for p in ["PANELA", "KIT", "BOLSA", "MOCHILA", "ORGANIZADOR", "POTE", "COTURNO", "LUMINÁRIA", "GARRAFA", "COPO"]):
        return "ITEM INDISPENSÁVEL PARA CASA NO PRECIN 🤌"
    elif any(p in nome_upper for p in ["VESTIDO", "CAMISA", "CALÇA", "BLUSA", "SHORT", "BERMUDA", "CASACO", "JAQUETA", "CONJUNTO"]):
        return "LOOK COMPLETO POR UM VALOR IMPERDÍVEL 👗"
    elif any(p in nome_upper for p in ["WHEY", "CREATINA", "SUPLEMENTO", "HALTER", "TAPETE", "YOGA", "ESPORTE", "GARRAFA MOTIVACIONAL"]):
        return "FOCO TOTAL NO TREINO COM ECONOMIA 🏋️‍♂️"
    elif any(p in nome_upper for p in ["BRINQUEDO", "BONECA", "CARRINHO", "INFANTIL", "BEBÊ", "FRALDA", "ESCOVA INFANTIL"]):
        return "ACHADO ESPECIAL PARA OS PEQUENOS 🧸"
    else:
        return "OPORTUNIDADE ÚNICA LIBERADA NA PLATAFORMA 🚀"

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    texto = (
        "🤖 *Casify - Painel Master 3.0*\n\n"
        "Tudo pronto para garimpar as melhores ofertas!\n\n"
        "💡 *Comandos disponíveis:*\n"
        "• Digite qualquer produto (ex: `fone bluetooth`, `tenis nike`) para gerar as **3 opções** formatadas.\n"
        "• Envie qualquer link da Shopee para conversão instantânea.\n"
        "• `/fila` - Visualizar rascunhos salvos.\n"
        "• `/limparfila` - Apagar rascunhos."
    )
    bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['fila'])
def ver_fila(message):
    if not FILA_RASCUNHOS:
        bot.reply_to(message, "📭 A fila de rascunhos está vazia no momento.")
    else:
        bot.reply_to(message, f"📋 Você tem **{len(FILA_RASCUNHOS)}** oferta(s) salva(s) na fila para postagem.", parse_mode="Markdown")

@bot.message_handler(commands=['limparfila'])
def limpar_fila(message):
    global FILA_RASCUNHOS
    FILA_RASCUNHOS = []
    bot.reply_to(message, "🗑️ Fila de rascunhos limpa com sucesso!")

@bot.message_handler(func=lambda message: True)
def processar_mensagem(message):
    texto_usuario = message.text.strip()
    
    # Processamento de link direto enviado pelo usuário
    if "http://" in texto_usuario or "https://" in texto_usuario:
        bot.reply_to(message, "🔄 Processando link no padrão profissional...")
        link_afiliado = expandir_link_shopee(texto_usuario)
        
        texto_postagem = (
            "OFERTA ESPECIAL COM DESCONTO EXCLUSIVO 🔥\n\n"
            "✅ Achado Selecionado da Shopee\n\n"
            "🔥 *GARANTA O SEU NO LINK ABAIXO* 🔥\n\n"
            f"🔗 {link_afiliado}\n\n"
            "anúncio"
        )
        FILA_RASCUNHOS.append(texto_postagem)
        bot.send_message(message.chat.id, "📦 Link convertido, formatado e adicionado à fila!", parse_mode="Markdown")
        
    else:
        bot.reply_to(message, "🔍 Garimpando as melhores ofertas com IA...")
        produtos = consultar_shopee_api_multipla(texto_usuario)
        
        if produtos:
            chat_id = message.chat.id
            
            for index, produto in enumerate(produtos):
                nome_prod_raw = produto.get("productName", texto_usuario)
                preco_raw = produto.get("price", "0")
                preco_max_raw = produto.get("priceMax")
                imagem_url = produto.get("imageUrl")
                link_afiliado = produto.get("offerLink") or produto.get("productLink", "https://shopee.com.br")
                
                nome_prod = escapar_markdown(nome_prod_raw)
                preco_formatado = formatar_preco(preco_raw)
                gancho_topo = gerar_gancho_promosam(nome_prod_raw)
                
                # Cálculo de parcelamento automático sem juros
                trecho_parcelamento = ""
                try:
                    p_val = float(preco_raw)
                    if p_val > 100:
                        parcelas = 10 if p_val > 300 else 4
                        v_parcela = p_val / parcelas
                        v_parc_fmt = formatar_preco(v_parcela)
                        trecho_parcelamento = f" em até {parcelas}x R$ {v_parc_fmt} sem juros"
                except:
                    pass
                
                # Bloco de Preços De/Por/Desconto
                bloco_preco = f"🔥 POR {preco_formatado}{trecho_parcelamento} 🔥\n\n"
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
                
                # Aviso de Frete Grátis e Cupom
                trecho_extras = "🚚 Possibilidade de Frete Grátis pelo App\n🎟️ Cupom: APLICAR NA PÁGINA\n\n"
                
                # Montagem final da postagem
                texto_postagem = (
                    f"{gancho_topo}\n\n"
                    f"✅ {nome_prod}\n\n"
                    f"{bloco_preco}"
                    f"{trecho_extras}"
                    f"🔗 {link_afiliado}\n\n"
                    "anúncio"
                )
                
                # Botão interativo rápido
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
            bot.send_message(message.chat.id, f"⚠️ Nenhum resultado encontrado para '{texto_usuario}'. Tente buscar com outras palavras.", parse_mode="Markdown")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot Casify Master 3.0 iniciado com sucesso!")
    bot.infinity_polling()
