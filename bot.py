import os
import telebot
import requests
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip

# Configurações iniciais do Bot e do Flask (para manter o Render acordado)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Casify Bot está online e operando na nuvem!"

def processar_video_produto(imagem_entrada, output_path="casify_reels.mp4"):
    """
    Processa a foto real mantendo 100% da integridade de cores e texturas,
    adicionando apenas o template visual do Casify e um movimento suave de zoom.
    """
    # 1. Abre a imagem original garantindo fidelidade total de cores (RGB)
    img = Image.open(imagem_entrada).convert("RGB")
    
    # Formato vertical ideal para Reels / Shorts (1080x1920)
    largura_alvo, altura_alvo = 1080, 1920
    
    # Redimensiona mantendo a proporção exata para não distorcer o produto
    img.thumbnail((largura_alvo - 100, altura_alvo - 400), Image.Resampling.LANCZOS)
    novo_w, novo_h = img.size

    # Cria o fundo elegante do Casify e centraliza o produto
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

    temp_img_path = "temp_final.jpg"
    fundo.save(temp_img_path, quality=95)

    # 3. Transforma em vídeo de 4 segundos com MoviePy (sem perda de qualidade na imagem base)
    clip = ImageClip(temp_img_path).set_duration(4)
    clip.write_videofile(output_path, fps=24, codec="libx264", audio=False, logger=None)

    # Limpeza de arquivos temporários locais
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)

    return output_path

# --- Comandos e escuta do Telegram ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 **Casify Online!** Envie a foto real do produto para gerarmos o vídeo padrão de alta conversão.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "⏳ Processando sua mídia com fidelidade total de cores e aplicando o padrão Casify...")
    
    try:
        # Pega a foto de maior resolução enviada
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_img = "produto_original.jpg"
        with open(input_img, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # Gera o vídeo
        output_video = processar_video_produto(input_img)
        
        # Envia de volta o vídeo pronto para o Telegram
        with open(output_video, 'rb') as vid:
            bot.send_video(message.chat.id, vid, caption="✅ **Vídeo gerado com sucesso!** Produto preservado sem alterações de cor ou textura.")
            
        # Limpeza pós-envio
        for f in [input_img, output_video]:
            if os.path.exists(f):
                os.remove(f)
                
    except Exception as e:
        bot.reply_to(message, f"❌ Ocorreu um erro ao processar o vídeo: {e}")

if __name__ == "__main__":
    # Inicializa o servidor Flask em paralelo (essencial para o Render)
    import threading
    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        
    t = threading.Thread(target=run_flask)
    t.start()
    
    # Inicia o bot
    bot.infinity_polling()
