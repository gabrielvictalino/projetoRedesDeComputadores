import socket

HOST = "127.0.0.1"
PORT = 5000

# ─── Cifra de César (criptografia simétrica manual) ───────────────────────────
# Mesma implementação do cliente. CHAVE_CESAR deve ser igual nos dois lados.
CHAVE_CESAR = 3

def cifrar_cesar(texto, chave=CHAVE_CESAR):
    resultado = ""
    for c in texto:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            resultado += chr((ord(c) - base + chave) % 26 + base)
        else:
            resultado += c
    return resultado

def decifrar_cesar(texto, chave=CHAVE_CESAR):
    return cifrar_cesar(texto, 26 - (chave % 26))

# ─── CRC-8 (integridade manual) ───────────────────────────────────────────────
# Idêntico ao cliente. Polinômio 0x07, implementado bit-a-bit.

def calcular_crc8(dados):
    POLINOMIO = 0x07
    crc = 0x00
    for byte in dados.encode('utf-8'):
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) & 0xFF) ^ POLINOMIO
            else:
                crc = (crc << 1) & 0xFF
    return crc

# ─── Checksum simples (mantido da entrega anterior) ───────────────────────────

def calcular_checksum(payload):
    return sum(ord(c) for c in payload) % 256

def montar_pacote(seq, payload):
    checksum = calcular_checksum(payload)
    crc = calcular_crc8(payload)
    return f"DATA;seq={seq};payload={payload};checksum={checksum};crc={crc}"

def validar_pacote(campos):
    """
    Retorna (valido, motivo_erro).
    Verifica checksum e, se presente, o CRC-8.
    """
    payload = campos.get("payload", "")

    checksum_recebido = int(campos.get("checksum", -1))
    if checksum_recebido != calcular_checksum(payload):
        return False, "checksum"

    if "crc" in campos:
        crc_recebido = int(campos.get("crc", -1))
        if crc_recebido != calcular_crc8(payload):
            return False, "crc8"

    return True, None

# ─── Parser de pacotes ────────────────────────────────────────────────────────

def extrair_pacote_data(mensagem):
    partes = mensagem.split(";")
    if partes[0] != "DATA":
        return None

    campos = {}
    for parte in partes[1:]:
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            campos[chave] = valor

    seq = int(campos.get("seq", -1))
    payload = campos.get("payload", "")
    return seq, payload, campos

# ─── Socket ───────────────────────────────────────────────────────────────────

def criar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR evita "Address already in use" ao reiniciar rapidamente
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen(1)
    print(f"Servidor iniciado em {HOST}:{PORT}")
    return servidor_socket

def aceitar_conexao(servidor_socket):
    conexao, endereco = servidor_socket.accept()
    print(f"Cliente conectado: {endereco}")
    return conexao

# ─── Handshake ────────────────────────────────────────────────────────────────

def tratar_handshake(conexao, mensagem):
    partes = mensagem.split(";")
    if partes[0] != "HANDSHAKE":
        return None

    campos = {}
    for parte in partes[1:]:
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            campos[chave] = valor

    modo_operacao = campos.get("modo", "GBN")
    usar_cifra = campos.get("cifra", "nao") == "sim"

    print(f"[SERVIDOR] Recebi do cliente: {mensagem}")
    print(f"[SERVIDOR] Modo: {modo_operacao} | Cifra de César: {'ativada' if usar_cifra else 'desativada'}")

    janela = 5
    resposta = f"Mensagem recebida com sucesso! Janela : {janela}"
    conexao.sendall((resposta + "\n").encode("utf-8"))
    print(f"[SERVIDOR] Enviei para o cliente: {resposta}\n")

    return modo_operacao, janela, usar_cifra

# ─── Loop principal de recebimento ────────────────────────────────────────────

def loop_recebimento(conexao, seq_inicial):
    buffer = ""
    pacotes_recebidos = {}
    handshake_recebido = False
    seqEsperado = seq_inicial
    seq_base = seq_inicial
    modo_operacao = "GBN"
    janela = 5
    usar_cifra = False
    pacotes_ok_consecutivos = 0  # rastreia acertos seguidos para aumentar janela

    while True:
        try:
            data = conexao.recv(1024)
        except Exception as e:
            print(f"[SERVIDOR] Erro ao receber dados: {e}")
            return pacotes_recebidos, False, seqEsperado, usar_cifra

        if not data:
            return pacotes_recebidos, False, seqEsperado, usar_cifra

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            mensagem = linha.strip()
            if not mensagem:
                continue

            # Fase de handshake
            if not handshake_recebido:
                resultado_hs = tratar_handshake(conexao, mensagem)
                if resultado_hs is not None:
                    modo_operacao, janela, usar_cifra = resultado_hs
                    handshake_recebido = True
                continue

            # Fim de transmissão
            if mensagem == "END":
                print(f"[SERVIDOR] Recebi END. Confirmando até seq={seqEsperado}")
                try:
                    if seqEsperado > seq_base:
                        conexao.sendall(f"ACK {seqEsperado}, Janela {janela}\n".encode())
                    conexao.sendall(b"ACK END\n")
                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                    print(f"[SERVIDOR] Aviso: cliente encerrou antes de receber ACK END ({e})")
                return pacotes_recebidos, False, seqEsperado, usar_cifra

            # Processa pacote de dados
            resultado = extrair_pacote_data(mensagem)
            if resultado is None:
                print("[SERVIDOR] Pacote em formato inesperado.")
                continue

            seq_recebido, payload, campos = resultado

            # Valida integridade (checksum + CRC-8)
            valido, motivo_erro = validar_pacote(campos)
            if not valido:
                janela = max(janela - 1, 1)
                pacotes_ok_consecutivos = 0
                print(f"[SERVIDOR] Falha de integridade ({motivo_erro}) para seq={seq_recebido}. Janela reduzida para {janela}. Enviando NACK.")
                if modo_operacao == "GBN":
                    conexao.sendall(f"NACK {seqEsperado}, Janela {janela}\n".encode())
                else:
                    conexao.sendall(f"NACK {seq_recebido}, Janela {janela}\n".encode())
                continue

            # ── GBN ──────────────────────────────────────────────────────────
            if modo_operacao == "GBN":
                if seq_recebido != seqEsperado:
                    print(f"[SERVIDOR] Fora de sequência. Recebido seq={seq_recebido}, esperado seq={seqEsperado}")
                    janela = max(janela - 1, 1)
                    pacotes_ok_consecutivos = 0
                    print(f"[SERVIDOR] Janela reduzida para {janela}")
                    conexao.sendall(f"NACK {seqEsperado}, Janela {janela}\n".encode())
                    continue

                seqEsperado += 4
                pacotes_ok_consecutivos += 1
                print(f"[SERVIDOR] Recebido: seq={seq_recebido}, payload='{payload}', checksum=OK, crc=OK")
                pacotes_recebidos[seq_recebido] = payload

                # ACK cumulativo ao completar janela
                janela_bytes = 4 * janela
                if (seqEsperado - seq_base) >= janela_bytes:
                    janela = min(janela + 1, 5)
                    pacotes_ok_consecutivos = 0
                    print(f"[SERVIDOR] Janela completa! Janela aumentada para {janela}. Enviando ACK seq={seqEsperado}")
                    conexao.sendall(f"ACK {seqEsperado}, Janela {janela}\n".encode())
                    seq_base = seqEsperado

            # ── RS ───────────────────────────────────────────────────────────
            elif modo_operacao == "RS":
                if seq_recebido in pacotes_recebidos:
                    print(f"[SERVIDOR-RS] Duplicata seq={seq_recebido}, reenviando ACK")
                    conexao.sendall(f"ACK {seq_recebido}, Janela {janela}\n".encode())
                    continue

                print(f"[SERVIDOR-RS] Recebido: seq={seq_recebido}, payload='{payload}', checksum=OK, crc=OK")
                pacotes_recebidos[seq_recebido] = payload
                pacotes_ok_consecutivos += 1

                # Aumenta janela a cada 'janela' pacotes corretos consecutivos
                if pacotes_ok_consecutivos >= janela:
                    janela = min(janela + 1, 5)
                    pacotes_ok_consecutivos = 0
                    print(f"[SERVIDOR-RS] Janela aumentada para {janela}")

                conexao.sendall(f"ACK {seq_recebido}, Janela {janela}\n".encode())

# ─── Reconstrução e exibição da mensagem ─────────────────────────────────────

def reconstruir_mensagem(pacotes_recebidos, usar_cifra):
    """Ordena pacotes por número de sequência e reconstrói o texto original."""
    if not pacotes_recebidos:
        return ""
    chaves_ordenadas = sorted(pacotes_recebidos.keys())
    texto = "".join(pacotes_recebidos[k] for k in chaves_ordenadas)
    if usar_cifra:
        texto = decifrar_cesar(texto)
    return texto

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    servidor_socket = criar_servidor()
    conexao = aceitar_conexao(servidor_socket)

    pacotes_recebidos, _, _, usar_cifra = loop_recebimento(conexao, seq_inicial=0)

    conexao.close()
    servidor_socket.close()
    print("\nServidor encerrado.")

    print(f"\n{'=' * 50}")
    print("MENSAGEM RECONSTRUÍDA:")
    mensagem_final = reconstruir_mensagem(pacotes_recebidos, usar_cifra)
    print(f"  {mensagem_final}")
    print(f"{'=' * 50}")
    print(f"Total de pacotes recebidos: {len(pacotes_recebidos)}")

if __name__ == "__main__":
    main()