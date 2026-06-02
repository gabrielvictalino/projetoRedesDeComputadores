import socket
import random
HOST = "127.0.0.1"
PORT = 5000

def descriptografar(texto_criptografado, chave):
    """Descriptografa um texto criptografado com Cifra de César"""
    chave_inversa = (26 - chave) % 26
    resultado = []
    for caractere in texto_criptografado:
        if caractere.isalpha():
            if caractere.isupper():
                pos = ord(caractere) - ord('A')
                nova_pos = (pos + chave_inversa) % 26
                resultado.append(chr(ord('A') + nova_pos))
            else:
                pos = ord(caractere) - ord('a')
                nova_pos = (pos + chave_inversa) % 26
                resultado.append(chr(ord('a') + nova_pos))
        else:
            resultado.append(caractere)
    return ''.join(resultado)


def calcular_checksum(payload):
    return sum(ord(c) for c in payload) % 256


def montar_pacote(seq, payload):
    checksum = calcular_checksum(payload)
    return f"DATA;seq={seq};payload={payload};checksum={checksum}"


def validar_pacote(campos):
    payload = campos.get("payload", "")
    checksum_recebido = int(campos.get("checksum", -1))
    checksum_calculado = calcular_checksum(payload)
    return checksum_recebido == checksum_calculado



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





def criar_servidor():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen(1)

    print(f"servidor iniciado em {HOST}:{PORT}")
    return servidor_socket


def aceitar_conexao(servidor_socket):
    conexao, endereco = servidor_socket.accept()
    print(f"cliente conectado: {endereco}")
    return conexao


def tratar_handshake(conexao, mensagem):
    partes = mensagem.split(";")

    if partes[0] != "HANDSHAKE":
        return None

    campos = {}
    for parte in partes[1:]:
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            campos[chave] = valor

    modo_operacao = campos.get("modo", "")
    chave_criptografia = int(campos.get("chave", 0))
    

    print(f"[SERVIDOR] Recebi do cliente: {mensagem}")
    print(f"[SERVIDOR] Modo: {modo_operacao}, Chave de criptografia: {chave_criptografia}")
    janela = 5
    resposta = f"Mensagem recebida com sucesso! Janela : {janela}"
    conexao.sendall((resposta + "\n").encode("utf-8"))

    print(f"[SERVIDOR] Enviei para o cliente: {resposta}\n")
    return modo_operacao, janela, chave_criptografia


def processar_mensagem(conexao, mensagem, seqEsperado, pacotes_recebidos,janela):
    if mensagem == "END":
        print("[SERVIDOR] Recebi mensagem de fim (END).")
        return False, seqEsperado

    print(f"[SERVIDOR] Recebi pacote bruto: {mensagem}")

    resultado = extrair_pacote_data(mensagem)
    if resultado is None:
        print("[SERVIDOR] Pacote em formato inesperado.")
        return True, seqEsperado

    seq, payload, campos = resultado
    
    if not validar_pacote(campos):
        print(f"[SERVIDOR] Checksum inválido para seq={seq}. Esperado seq={seqEsperado}")
        conexao.sendall(f"NACK {seqEsperado}\n".encode())
        return True, seqEsperado  # Continua recebendo, não sai
    
    if seq != seqEsperado:
        print(f"[SERVIDOR] Pacote fora de sequência. Recebido seq={seq}, esperado seq={seqEsperado}")
        conexao.sendall(f"NACK {seqEsperado}\n".encode())
        return True, seqEsperado  # Continua recebendo, não sai

    # Pacote correto - incrementa sequência
    seqEsperado += 4
    print(f"[SERVIDOR] Metadados - seq={seq}, payload='{payload}'")
    pacotes_recebidos[seq] = payload

    return True, seqEsperado


def loop_recebimento(conexao, seq):
    buffer = ""
    pacotes_recebidos = {}
    handshake_recebido = False
    seqEsperado = seq
    seq_base = seq  # Primeira sequência da janela
    modo_operacao = ""
    janela = 0
    chave_criptografia = 0  # Inicializa a chave
    ultima_janela_incompleta = False  # Flag para ter certeza se é a última janela

    while True:
        try:
            data = conexao.recv(1024)
        except Exception as e:
            print(f"[SERVIDOR] Erro ao receber dados: {e}")
            return pacotes_recebidos, False, seqEsperado, chave_criptografia
        
        if not data:
            return pacotes_recebidos, False, seqEsperado, chave_criptografia

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            mensagem = linha.strip()

            if not mensagem:
                continue

            # Primeiro, aguarda o handshake
            if not handshake_recebido:
                resultado_hs = tratar_handshake(conexao, mensagem)
                if resultado_hs is not None:
                    modo_operacao, janela, chave_criptografia = resultado_hs
                    handshake_recebido = True
                continue

            # Depois processa mensagens de dados
            if mensagem == "END":
                print(f"[SERVIDOR] Recebi mensagem END. Confirmando lote até seq={seqEsperado}")
                # Envia ACK com última sequência confirmada (mesmo que janela incompleta)
                if seqEsperado > seq_base:
                    conexao.sendall(f"ACK {seqEsperado}, Janela {janela}\n".encode())
                conexao.sendall(f"ACK END\n".encode())
                return pacotes_recebidos, False, seqEsperado, chave_criptografia

            # Processa pacote de dados
            resultado = extrair_pacote_data(mensagem)
            if resultado is None:
                print("[SERVIDOR] Pacote em formato inesperado.")
                continue

            seq_recebido, payload, campos = resultado

            # Valida checksum
            if not validar_pacote(campos):
                print(f"[SERVIDOR] Checksum inválido para seq={seq_recebido}")
                conexao.sendall(f"NACK {seq_recebido}\n".encode())
                continue

            # Processa conforme protocolo
            if modo_operacao == "GBN":
                # Verifica se é o próximo esperado (sequência estrita)
                if seq_recebido != seqEsperado:
                    print(f"[SERVIDOR] Pacote fora de sequência. Recebido seq={seq_recebido}, esperado seq={seqEsperado}")
                    conexao.sendall(f"NACK {seqEsperado}\n".encode())
                    continue

                # Pacote correto
                seqEsperado += 4
                print(f"[SERVIDOR] Recebido: seq={seq_recebido}, payload='{payload}'")
                pacotes_recebidos[seq_recebido] = payload

                # Envia ACK quando completa uma janela inteira
                janela_size = 4 * janela
                if (seqEsperado - seq_base) >= janela_size:
                    print(f"[SERVIDOR] Janela completa! Enviando ACK para seq={seqEsperado}")
                    conexao.sendall(f"ACK {seqEsperado}, Janela {janela}\n".encode())
                    seq_base = seqEsperado

            elif modo_operacao == "RS":
                # Repetição Seletiva: aceita pacotes fora de ordem
                # Se já recebido, ignora duplicata
                if seq_recebido in pacotes_recebidos:
                    print(f"[SERVIDOR-RS] Pacote duplicado seq={seq_recebido}, reenviando ACK")
                    conexao.sendall(f"ACK {seq_recebido}\n".encode())
                    continue

                # Recebe o pacote (mesmo se fora de ordem)
                print(f"[SERVIDOR-RS] Recebido: seq={seq_recebido}, payload='{payload}'")
                pacotes_recebidos[seq_recebido] = payload

                # Envia ACK imediatamente para este pacote
                conexao.sendall(f"ACK {seq_recebido}\n".encode())
    
    


def main():
    servidor_socket = criar_servidor()
    conexao = aceitar_conexao(servidor_socket)
    
    seq = 0
    pacotes_recebidos, fim, _, chave_criptografia = loop_recebimento(conexao, seq)
    
    conexao.close()
    servidor_socket.close()

    print("servidor encerrado")
    print("pacotes recebidos:", pacotes_recebidos)
    
    # Reconstrói a mensagem original a partir dos pacotes
    if pacotes_recebidos:
        mensagem_criptografada = ''.join(pacotes_recebidos[seq] for seq in sorted(pacotes_recebidos.keys()))
        print(f"\n Mensagem criptografada recebida: {mensagem_criptografada}")
        
        # Descriptografa a mensagem
        if chave_criptografia > 0:
            mensagem_original = descriptografar(mensagem_criptografada, chave_criptografia)
            print(f" Mensagem descriptografada: {mensagem_original}")
        else:
            print(" Chave de criptografia não fornecida!")


if __name__ == "__main__":
    main()
