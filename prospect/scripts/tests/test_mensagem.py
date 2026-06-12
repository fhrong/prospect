import sys
import os
import base64

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.messaging import criar_instancia, status_instancia, enviar_mensagem, montar_mensagem, deletar_instancia

INSTANCIA = "teste_local"
NUMERO    = "5516992616267"

# 1. Deleta se existir e cria do zero
deletar_instancia(INSTANCIA)
resultado = criar_instancia(INSTANCIA)

# 2. Salva o QR como imagem
qr_base64 = resultado.get("qrcode", {}).get("base64", "")
if qr_base64:
    dados = qr_base64.split(",")[1] if "," in qr_base64 else qr_base64
    with open("qrcode.png", "wb") as f:
        f.write(base64.b64decode(dados))
    print("QR Code salvo em qrcode.png — abra o arquivo e escaneie.")

input("\nEscaneie o QR e pressione ENTER para continuar...")

# 3. Confirma conexão
estado = status_instancia(INSTANCIA)
print(f"Status da instância: {estado}")

if estado != "open":
    print("Instância não conectada. Tente escanear novamente.")
    sys.exit(1)

# 4. Envia mensagem de teste
texto = montar_mensagem("contabilidade", "ABC Contabilidade", "Ribeirão Preto")
print(f"\nMensagem:\n{texto}")

resposta = enviar_mensagem(INSTANCIA, NUMERO, texto)
print(f"\nResposta da Evolution: {resposta}")