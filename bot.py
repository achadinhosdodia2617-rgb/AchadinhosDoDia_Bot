import os
import telebot
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

# Configurações iniciais do Bot e do Flask
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise Exception("Bot token is not defined")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Casify Bot está online e operando na nuvem!"

def processar_foto_produto(imagem_entrada, output_path="casify_post.jpg"):
    """
    Processa a foto real mantendo 100% da integridade de cores e texturas,
    aplicando o template visual elegante do Casify ao redor da imagem.
    """
    # 1. Abre a imagem original garantindo fidelidade total de cores (RGB)
    img = Image.open(imagem_entrada).convert("RGB")
    
    # Formato vertical ideal para redes sociais (1080x1920)
    largura_alvo, altura_alvo = 1080, 1920
    
    # Redimensiona mantendo a proporção exata para não distorcer o produto
    img.thumbnail((largura_alvo - 100, altura_alvo - 400), Image.Resampling.LANCZOS)
    novo_w, novo_h = img.size

    # Cria o fundo elegante do Casify e centraliza o produto perfeitamente
    fundo = Image.new("RGB", (largura_alvo, altura_alvo), (18, 18, 18))
    offset_x = (largura_alvo - novo_w) // 2
    offset_y = (altura_alvo - novo_h) // 2
    fundo.paste(img, (offset_x, offset_y))

    # 2. Adiciona o cabeçalho e marca d'água oficial do Casify
    draw = ImageDraw.Draw(fundo)
    try:
        fonte = ImageFont.truetype("arial.ttf", 40)
    except:
        fonte = ImageFont.load_default()

    # Faixa superior limpa
    draw.rectangle([(40, 60), (1040, 160)], fill=(0, 0, 0, 200))
    draw.text((70, 90), "✨ Casify • Achados Inteligentes", fill=(255, 255, 255), font=fonte)

    # Salva a imagem final processada com alta qualidade
    fundo.save(output_path, quality=95)
    return output_path

# --- Comandos e escuta do Telegram ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 **Casify Online!** Envie a foto real do produto para gerarmos a postagem padrão de alta conversão com fidelidade total.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "⏳ Processando sua mídia com fidelidade total de cores e aplicando o padrão Casify...")
    
    input_img = "produto_original.jpg"
    output_img = "produto_final.jpg"
    
    try:
        # Pega a foto de maior resolução enviada
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(input_img, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # Processa a imagem mantendo a integridade
        resultado = processar_foto_produto(input_img, output_img)
        
        # Envia de volta a foto pronta para o Telegram
        with open(resultado, 'rb') as foto_final:
            bot.send_photo(message.chat.id, foto_final, caption="✅ **Postagem gerada com sucesso!** Produto preservado sem alterações de cor ou textura.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ocorreu um erro ao processar a imagem: {e}")
        
    finally:
        # Limpeza de arquivos temporários locais
        for f in [input_img, output_img]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    # Inicializa o servidor Flask em paralelo (essencial para o Render)
    import threading
    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        
    t = threading.Thread(target=run_flask)
    t.start()
    
    # Inicia o bot
    bot.infinity_polling()
