import os
import subprocess
import sys
import json
import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- LEITURA SEGURA DAS CREDENCIAIS ---
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Verificação
if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("ERRO: Variáveis de ambiente não configuradas!")
    exit(1)

# ==================
# CONFIGURAÇÕES
# ==================
ADMINS = [6022965096, 7472622094]

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================
# LISTA DE BANNERS
# ==================
BANNERS = [
    os.path.join(os.getcwd(), "banners", "banner.jpg"),
    os.path.join(os.getcwd(), "banners", "banner2.jpg"),
    os.path.join(os.getcwd(), "banners", "banner3.jpg")
]

# ==================
# FUNÇÕES DE ARQUIVOS
# ==================
def carregar_usuarios():
    try:
        with open("usuarios.json", "r") as f:
            return json.load(f)
    except:
        return {}

def salvar_usuarios(data):
    with open("usuarios.json", "w") as f:
        json.dump(data, f, indent=4)

def carregar_estoque():
    try:
        with open("estoque.json", "r") as f:
            return json.load(f)
    except:
        return []

def salvar_estoque(data):
    with open("estoque.json", "w") as f:
        json.dump(data, f, indent=4)

# ==================
# MENU PRINCIPAL
# ==================
async def menu_principal(message, user_id):
    usuarios = carregar_usuarios()
    saldo = usuarios[user_id]["saldo"]

    texto = f"""
🔥 BINS DISPONÍVEIS NA LOJA 🔥

👤 ID: {user_id}
💰 Saldo: R$ {saldo}

━━━━━━━━━━━━━━

Escolha uma opção:
"""

    botoes = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Comprar", "comprar")],
        [InlineKeyboardButton("💰 Adicionar Saldo", "saldo")],
        [InlineKeyboardButton("👤 Perfil", "perfil")]
    ])

    # Escolhe banner aleatório e verifica se existe
    banner = random.choice(BANNERS)
    if not os.path.isfile(banner):
        await message.reply(texto, reply_markup=botoes)
        return

    try:
        # Tenta editar como legenda se mensagem anterior for foto
        await message.edit_caption(caption=texto, reply_markup=botoes)
    except:
        # Se não, envia foto
        await message.reply_photo(photo=banner, caption=texto, reply_markup=botoes)

# ==================
# COMANDO /START COM AFILIADOS
# ==================
@app.on_message(filters.command("start"))
async def start(client, message):
    usuarios = carregar_usuarios()
    user_id = str(message.from_user.id)

    # Verifica se há parametro de afiliado
    if len(message.command) > 1:
        ref_id = message.command[1]  # ID do indicante
    else:
        ref_id = None

    # Cria o usuário se não existir
    if user_id not in usuarios:
        usuarios[user_id] = {"saldo": 0, "comissao": 0}
        # Se veio por indicação, adiciona saldo e comissão para o indicante
        if ref_id and ref_id in usuarios and ref_id != user_id:
            usuarios[ref_id]["saldo"] += 2
            usuarios[ref_id]["comissao"] += 2
            await message.reply(f"✅ Usuário indicado! Saldo atualizado do indicante: R$ {usuarios[ref_id]['saldo']:.2f}")
        salvar_usuarios(usuarios)

    await menu_principal(message, user_id)

# ==================
# CALLBACKS
# ==================
@app.on_callback_query()
async def callbacks(client, callback):
    user_id = str(callback.from_user.id)
    usuarios = carregar_usuarios()
    saldo = usuarios[user_id]["saldo"]

    # PERFIL
    if callback.data == "perfil":
        agora = datetime.now()
        data_atual = agora.strftime("%d/%m/%Y")
        hora_atual = agora.strftime("%H:%M:%S")

        texto = f"""
👤 Suas informações
- Aqui você pode visualizar os detalhes da sua conta.

🏆 𝙎𝙀𝙐 𝙋𝙀𝙍𝙁𝙄𝙇
👤 Nome: {callback.from_user.first_name}
🆔 ID: {user_id}
📆 Data: {data_atual}
🕒 Hora: {hora_atual}

🃏 𝐋𝐈𝐍𝐊 𝐀𝐅𝐈𝐋𝐈𝐀𝐃𝐎
💰 Convide pessoas com seu link de afiliado e ganhe R$2 de saldo por indicação
🛍 Link: https://t.me/Paiva021_bot?start={user_id}

✨ ID: {user_id}
🪙 Saldo: R$ {saldo}
💸 Comissão: R$ {usuarios[user_id].get('comissao', 0):.2f}
"""
        botoes = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", "menu")]])
        await callback.message.edit_text(texto, reply_markup=botoes)

    # ADICIONAR SALDO
    elif callback.data == "saldo":
        texto = f"💰 ADICIONAR SALDO\n\nEnvie PIX para o ADM\nSeu ID: {user_id}"
        botoes = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", "menu")]])
        await callback.message.edit_text(texto, reply_markup=botoes)

    # COMPRAR BINS
    elif callback.data == "comprar":
        estoque = carregar_estoque()
        contador = {}
        for item in estoque:
            bin = item["gg"][:6]
            contador[bin] = contador.get(bin, 0) + 1

        texto = f"💳 BINS DISPONÍVEIS\n\n👤 ID: {user_id}\n💰 Saldo: R$ {saldo}"
        botoes = [[InlineKeyboardButton(f"{bin} ({qtd})", callback_data=f"bin_{bin}")] for bin, qtd in contador.items()]
        botoes.append([InlineKeyboardButton("🔙 Voltar", "menu")])
        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(botoes))

    # MOSTRAR PREÇO DO BIN
    elif "bin_" in callback.data:
        bin = callback.data.split("_")[1]
        estoque = carregar_estoque()
        lista = [item for item in estoque if item["gg"].startswith(bin)]
        if not lista:
            await callback.answer("Sem estoque")
            return
        preco = lista[0]["preco"]
        texto = f"💳 BIN: {bin}\n💰 Preço: R$ {preco}\nSaldo: R$ {saldo}"
        botoes = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Comprar", callback_data=f"buy_{bin}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="comprar")]
        ])
        await callback.message.edit_text(texto, reply_markup=botoes)

    # FINALIZAR COMPRA
    elif "buy_" in callback.data:
        bin = callback.data.split("_")[1]
        estoque = carregar_estoque()
        card = next((item for item in estoque if item["gg"].startswith(bin)), None)
        if not card:
            await callback.answer("Sem estoque")
            return
        preco = card["preco"]
        if saldo < preco:
            await callback.answer("Sem saldo")
            return

        usuarios[user_id]["saldo"] -= preco
        salvar_usuarios(usuarios)
        estoque.remove(card)
        salvar_estoque(estoque)

        numero, mes, ano, cvv = card["gg"].split("|")
        texto = f"✅ Compra Efetuada\n\n💳 Cartão: {numero}\n📆 Data: {mes}/{ano}\nCVV: {cvv}\n💰 Preço: R$ {preco}\n💰 Saldo restante: R$ {usuarios[user_id]['saldo']}"
        botoes = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", "menu")]])
        await callback.message.edit_text(texto, reply_markup=botoes)

    # VOLTAR MENU
    elif callback.data == "menu":
        await menu_principal(callback.message, user_id)

# ==================
# COMANDOS ADM
# ==================
@app.on_message(filters.command("addsaldo"))
async def addsaldo(client, message):
    if message.from_user.id not in ADMINS:
        return
    try:
        user = message.text.split()[1]
        valor = float(message.text.split()[2])
    except:
        await message.reply("Uso correto: /addsaldo <user_id> <valor>")
        return
    usuarios = carregar_usuarios()
    if user not in usuarios:
        usuarios[user] = {"saldo": 0, "comissao": 0}
    usuarios[user]["saldo"] += valor
    salvar_usuarios(usuarios)
    await message.reply("✅ Saldo adicionado")

@app.on_message(filters.command("addestoque"))
async def addestoque(client, message):
    if message.from_user.id not in ADMINS:
        return
    await message.reply("Envie no formato:\nnumero|mes|ano|cvv\npreco\nExemplo:\n4984013055519040|04|2027|999\n5")

@app.on_message(filters.private & filters.text)
async def receber_estoque(client, message):
    if message.from_user.id not in ADMINS:
        return
    linhas = message.text.strip().split("\n")
    if len(linhas) < 2:
        return
    try:
        preco = float(linhas[-1])
        itens = linhas[:-1]
        estoque = carregar_estoque()
        adicionados = 0
        for item in itens:
            estoque.append({"gg": item.strip(), "preco": preco})
            adicionados += 1
        salvar_estoque(estoque)
        await message.reply(f"✅ {adicionados} itens adicionados ao estoque")
    except:
        await message.reply("❌ Formato errado")

# ==================
# RUN BOT
# ==================
if __name__ == "__main__":
    print("BOT INICIANDO...")
    app.run()