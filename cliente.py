import socket

HOST = "127.0.0.1"
PORT = 5000

# ─── Cifra de César (criptografia simétrica manual) ───────────────────────────
# Desloca cada letra do alfabeto 'chave' posições.
# Chave compartilhada entre cliente e servidor (deve ser a mesma nos dois lados).
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
    # Decifrar é cifrar com o complemento: 26 - chave
    return cifrar_cesar(texto, 26 - (chave % 26))

# ─── CRC-8 (integridade manual) ───────────────────────────────────────────────
# Implementação bit-a-bit do CRC-8 com polinômio 0x07 (x^8 + x^2 + x + 1).
# Detecta: todos erros de 1 bit, burst errors até 7 bits, a maioria de 2 bits.
# Não usa nenhuma biblioteca externa — apenas operações bit-a-bit nativas do Python.

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

def validar_pacote(campos):
    payload = campos.get("payload", "")
    checksum_recebido = int(campos.get("checksum", -1))
    if checksum_recebido != calcular_checksum(payload):
        return False
    if "crc" in campos:
        crc_recebido = int(campos.get("crc", -1))
        if crc_recebido != calcular_crc8(payload):
            return False
    return True

# ─── Montagem e fragmentação de pacotes ──────────────────────────────────────

def fragmentar_texto(texto, tam_bloco=4):
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def montar_pacote(seq, payload):
    checksum = calcular_checksum(payload)
    crc = calcular_crc8(payload)
    return f"DATA;seq={seq};payload={payload};checksum={checksum};crc={crc}"

# ─── Simulação de Erros (Entrega 3) ──────────────────────────────────────────
# Erros são determinísticos: definidos pelo cliente antes do envio.
# 'CORRUPTO' → altera checksum e crc para forçar detecção de erro no servidor.
# 'PERDA'    → pacote não é enviado, simulando perda no canal.

def aplicar_erro_pacote(pacote, tipo_erro):
    if tipo_erro == 'PERDA':
        return None
    elif tipo_erro == 'CORRUPTO':
        partes = pacote.split(";")
        novos = []
        for p in partes:
            if p.startswith("checksum="):
                val = int(p.split("=")[1])
                novos.append(f"checksum={(val + 1) % 256}")
            elif p.startswith("crc="):
                val = int(p.split("=")[1])
                novos.append(f"crc={(val + 1) % 256}")
            else:
                novos.append(p)
        return ";".join(novos)
    return pacote

def get_pacote_para_envio(pacote, indice, erros, erros_ja_aplicados):
    """
    Retorna (deve_enviar, pacote_final).
    O erro é aplicado apenas na primeira transmissão do pacote.
    Retransmissões (após NACK/timeout) enviam o pacote correto.
    """
    if indice in erros and indice not in erros_ja_aplicados:
        erros_ja_aplicados.add(indice)
        modificado = aplicar_erro_pacote(pacote, erros[indice])
        if modificado is None:
            return False, None
        return True, modificado
    return True, pacote

def configurar_erros():
    """Solicita ao usuário quais pacotes devem ser corrompidos ou perdidos."""
    erros = {}
    simular = input("\nDeseja simular erros? (s/n): ").strip().lower()
    if simular != 's':
        return erros

    corrompidos = input("Índices dos pacotes para CORROMPER (ex: 0,2 ou vazio): ").strip()
    perdidos    = input("Índices dos pacotes para PERDER    (ex: 1,3 ou vazio): ").strip()

    for idx in corrompidos.split(","):
        idx = idx.strip()
        if idx.isdigit():
            erros[int(idx)] = 'CORRUPTO'

    for idx in perdidos.split(","):
        idx = idx.strip()
        if idx.isdigit():
            erros[int(idx)] = 'PERDA'

    if erros:
        print(f"[CLIENTE] Erros configurados: {erros}")
    return erros

# ─── Comunicação ──────────────────────────────────────────────────────────────

def enviar_linha(sock, mensagem):
    sock.sendall((mensagem + "\n").encode("utf-8"))

# ─── Go-Back-N ────────────────────────────────────────────────────────────────

def enviar_lote(comeco_do_envio, janela, pacotes, cliente_socket, erros, erros_ja_aplicados):
    """Envia uma janela de pacotes, aplicando erros determinísticos se configurado."""
    fim = min(comeco_do_envio + janela - 1, len(pacotes) - 1)
    print(f"\n[CLIENTE] Enviando lote da janela: índices {comeco_do_envio} a {fim}")

    for i in range(comeco_do_envio, min(comeco_do_envio + janela, len(pacotes))):
        deve_enviar, pacote_final = get_pacote_para_envio(pacotes[i], i, erros, erros_ja_aplicados)
        if not deve_enviar:
            print(f"  [CLIENTE] Pacote {i} PERDIDO (simulação de perda)")
        elif pacote_final != pacotes[i]:
            print(f"  [CLIENTE] Pacote {i} CORROMPIDO (simulação): {pacote_final}")
            enviar_linha(cliente_socket, pacote_final)
        else:
            enviar_linha(cliente_socket, pacote_final)
            print(f"  [CLIENTE] Enviado: {pacote_final}")

    return esperarAckOuNack_gbn(cliente_socket)

def esperarAckOuNack_gbn(cliente_socket):
    """Aguarda ACK/NACK do servidor com timeout de 5 segundos."""
    cliente_socket.settimeout(5)
    try:
        resposta = cliente_socket.recv(1024).decode("utf-8").strip()
        print(f"[CLIENTE] Recebi: {resposta}")
    except socket.timeout:
        print("[CLIENTE] TIMEOUT ao aguardar ACK da janela")
        return None

    if resposta.startswith("NACK"):
        partes_virgula = resposta.split(",")
        partes_nack = partes_virgula[0].split()
        if len(partes_nack) >= 2:
            nack_seq = int(partes_nack[1])
            nova_janela = int(partes_virgula[1].split()[-1]) if len(partes_virgula) > 1 else None
            sufixo = f", nova janela={nova_janela}" if nova_janela else ""
            print(f"[CLIENTE] NACK recebido — retransmitir a partir de seq={nack_seq}{sufixo}")
            resultado = f"NACK {nack_seq}"
            if nova_janela:
                resultado += f" janela={nova_janela}"
            return resultado

    elif resposta.startswith("ACK"):
        partes = resposta.split(",")
        partes1 = partes[0].split()
        if len(partes1) > 1:
            seq_confirmado = int(partes1[1])
            nova_janela = int(partes[1].split()[-1]) if len(partes) > 1 and "Janela" in partes[1] else None
            sufixo = f", nova janela={nova_janela}" if nova_janela else ""
            print(f"[CLIENTE] ACK recebido — janela confirmada até seq={seq_confirmado}{sufixo}")
            resultado = f"ACK {seq_confirmado}"
            if nova_janela:
                resultado += f" janela={nova_janela}"
            return resultado

    return None

# ─── Repetição Seletiva ───────────────────────────────────────────────────────

def enviar_lote_rs(pacotes, indices, cliente_socket, erros, erros_ja_aplicados):
    """Envia pacotes individuais (RS), aplicando erros determinísticos."""
    for i in indices:
        if i < len(pacotes):
            deve_enviar, pacote_final = get_pacote_para_envio(pacotes[i], i, erros, erros_ja_aplicados)
            if not deve_enviar:
                print(f"  [CLIENTE-RS] Pacote {i} PERDIDO (simulação de perda)")
            elif pacote_final != pacotes[i]:
                print(f"  [CLIENTE-RS] Pacote {i} CORROMPIDO (simulação): {pacote_final}")
                enviar_linha(cliente_socket, pacote_final)
            else:
                enviar_linha(cliente_socket, pacote_final)
                print(f"  [CLIENTE-RS] Enviado: {pacote_final}")

def receber_acks_rs(cliente_socket, confirmados, total_pacotes):
    """
    Recebe múltiplos ACKs e NACKs do servidor.
    NACK marca o pacote como não confirmado para retransmissão.
    Retorna (acks_recebidos, ultima_janela_vista) — janela=None se não informada.
    """
    cliente_socket.settimeout(2)
    acks_recebidos = 0
    ultima_janela_vista = None

    try:
        while True:
            try:
                dados = cliente_socket.recv(1024).decode("utf-8").strip()
                if not dados:
                    break

                # Um recv pode conter múltiplas respostas em sequência rápida
                for linha in dados.split("\n"):
                    linha = linha.strip()
                    if not linha:
                        continue

                    if linha.startswith("ACK") and "END" not in linha:
                        # Formato: "ACK {seq}, Janela {n}"
                        partes_virgula = linha.split(",")
                        partes_ack = partes_virgula[0].split()
                        seq_confirmado = int(partes_ack[1])
                        if len(partes_virgula) > 1 and "Janela" in partes_virgula[1]:
                            ultima_janela_vista = int(partes_virgula[1].split()[-1])
                        indice = seq_confirmado // 4
                        if 0 <= indice < total_pacotes:
                            confirmados[indice] = True
                            print(f"[CLIENTE-RS] Confirmado pacote {indice} (seq={seq_confirmado})")
                            acks_recebidos += 1

                    elif linha.startswith("NACK"):
                        # Formato: "NACK {seq}, Janela {n}"
                        partes_virgula = linha.split(",")
                        partes_nack = partes_virgula[0].split()
                        seq_nack = int(partes_nack[1])
                        if len(partes_virgula) > 1 and "Janela" in partes_virgula[1]:
                            ultima_janela_vista = int(partes_virgula[1].split()[-1])
                        indice = seq_nack // 4
                        print(f"[CLIENTE-RS] NACK recebido — pacote {indice} (seq={seq_nack}) será retransmitido")
                        if 0 <= indice < total_pacotes:
                            confirmados[indice] = False

            except socket.timeout:
                break
    except Exception as e:
        print(f"[CLIENTE-RS] Erro ao receber ACKs: {e}")

    return acks_recebidos, ultima_janela_vista

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect((HOST, PORT))
    print(f"Conectado ao servidor em {HOST}:{PORT}")

    modo_operacao = input("Digite o modo de operação: (GBN)/(RS) ").strip().upper()
    usar_cifra = input("Usar cifra de César? (s/n): ").strip().lower() == 's'

    handshake_msg = f"HANDSHAKE;modo={modo_operacao};cifra={'sim' if usar_cifra else 'nao'}"
    enviar_linha(cliente_socket, handshake_msg)
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8").strip()
    resposta_separada = resposta.split("!")
    respostaSeparadaJanela = resposta_separada[1].split(":")
    respostaSeparadaJanela = respostaSeparadaJanela[1].strip()

    print(f"[CLIENTE] Recebi do servidor: {resposta}\n")
    janela = int(respostaSeparadaJanela)

    texto = input("Digite a mensagem a ser enviada (min de 30 caracteres): ")
    if len(texto) < 30:
        print("A mensagem deve conter pelo menos 30 caracteres.")
        cliente_socket.close()
        return

    # Aplica cifra de César antes de fragmentar
    if usar_cifra:
        texto_para_envio = cifrar_cesar(texto)
        print(f"[CLIENTE] Texto cifrado (César): {texto_para_envio}")
    else:
        texto_para_envio = texto

    # Configura simulação de erros determinísticos (Entrega 3)
    erros = configurar_erros()
    erros_ja_aplicados = set()

    blocos = fragmentar_texto(texto_para_envio, tam_bloco=4)
    total_pacotes = len(blocos)
    print(f"[CLIENTE] Texto será enviado em {total_pacotes} pacotes.\n")

    arrPacotes = []
    seq = 0
    for payload in blocos:
        arrPacotes.append(montar_pacote(seq, payload))
        seq += 4

    # ── Repetição Seletiva ────────────────────────────────────────────────────
    if modo_operacao == "RS":
        print(f"[CLIENTE] Iniciando Repetição Seletiva. Janela: {janela} pacotes\n")
        confirmados = [False] * total_pacotes
        base = 0
        tentativas_sem_progresso = 0
        max_tentativas = 5

        while base < total_pacotes:
            fim_janela = min(base + janela, total_pacotes)
            indices_nao_confirmados = [i for i in range(base, fim_janela) if not confirmados[i]]

            if not indices_nao_confirmados:
                # Todos confirmados nesta janela, avança base
                while base < total_pacotes and confirmados[base]:
                    base += 1
                continue

            print(f"[CLIENTE-RS] Enviando janela: índices {base} a {fim_janela - 1}")
            enviar_lote_rs(arrPacotes, indices_nao_confirmados, cliente_socket, erros, erros_ja_aplicados)

            acks, nova_janela = receber_acks_rs(cliente_socket, confirmados, total_pacotes)
            if nova_janela is not None and nova_janela != janela:
                print(f"[CLIENTE-RS] Janela atualizada pelo servidor: {janela} → {nova_janela}")
                janela = nova_janela
            print(f"[CLIENTE-RS] Recebido {acks} ACK(s) nesta iteração | Janela atual: {janela}\n")

            if acks == 0:
                tentativas_sem_progresso += 1
                if tentativas_sem_progresso >= max_tentativas:
                    print("[CLIENTE-RS] Máximo de tentativas sem progresso. Abortando.")
                    break
            else:
                tentativas_sem_progresso = 0

            while base < total_pacotes and confirmados[base]:
                base += 1

        print("[CLIENTE] Todos os pacotes foram enviados!")

    # ── Go-Back-N ─────────────────────────────────────────────────────────────
    else:
        print(f"[CLIENTE] Iniciando Go-Back-N. Janela: {janela} pacotes")
        comeco_envio = 0
        tentativas = 0
        max_tentativas = 5

        while comeco_envio < len(arrPacotes):
            eh_ultima_janela = (comeco_envio + janela) >= len(arrPacotes)

            resposta = enviar_lote(comeco_envio, janela, arrPacotes, cliente_socket, erros, erros_ja_aplicados)

            if resposta is None:
                # Timeout: última janela incompleta não gera ACK do servidor
                if eh_ultima_janela:
                    print("[CLIENTE] Última janela enviada sem ACK. Encerrando...")
                    comeco_envio = len(arrPacotes)
                    break
                tentativas += 1
                if tentativas > max_tentativas:
                    print("[CLIENTE] Máximo de tentativas excedido!")
                    break
                print(f"[CLIENTE] Timeout — retransmitindo janela (tentativa {tentativas})...")
                continue

            tentativas = 0

            # Extrai e aplica novo tamanho de janela se o servidor o enviou
            if " janela=" in resposta:
                partes_j = resposta.split(" janela=")
                nova_janela = int(partes_j[1])
                if nova_janela != janela:
                    print(f"[CLIENTE] Janela atualizada pelo servidor: {janela} → {nova_janela}")
                janela = nova_janela
                resposta = partes_j[0]  # remove o sufixo para o parsing abaixo

            if resposta.startswith("ACK"):
                seq_confirmado = int(resposta.split()[1])
                novo_comeco = seq_confirmado // 4
                if novo_comeco > comeco_envio:
                    comeco_envio = novo_comeco
                    print(f"[CLIENTE] Progresso: agora nos índices {comeco_envio}+")
                else:
                    tentativas += 1

            elif resposta.startswith("NACK"):
                nack_seq = int(resposta.split()[1])
                comeco_envio = nack_seq // 4
                print(f"[CLIENTE] Retransmitindo a partir do índice {comeco_envio}")

        print("[CLIENTE] Todos os pacotes foram enviados!")

    # ── Encerramento ──────────────────────────────────────────────────────────
    enviar_linha(cliente_socket, "END")
    print("[CLIENTE] Enviei mensagem de fim: END")

    # Reseta o timeout herdado dos loops de envio antes de aguardar o encerramento.
    # O servidor pode enviar até duas mensagens ("ACK X, Janela N" + "ACK END"),
    # portanto lemos em loop até receber "ACK END" explicitamente.
    cliente_socket.settimeout(10)
    try:
        buffer_final = ""
        while True:
            data = cliente_socket.recv(1024)
            if not data:
                break
            buffer_final += data.decode("utf-8")
            for linha in buffer_final.split("\n"):
                linha = linha.strip()
                if linha:
                    print(f"[CLIENTE] Recebi do servidor: {linha}")
            if "ACK END" in buffer_final:
                break
        print("Conexão encerrada com sucesso!")
    except Exception as e:
        print(f"[CLIENTE] Erro ao receber resposta final: {e}")
    finally:
        cliente_socket.close()

if __name__ == "__main__":
    main()