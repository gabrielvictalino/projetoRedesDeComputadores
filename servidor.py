import socket
import random

HOST = "127.0.0.1"
PORT = 5000


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
    

    print(f"[SERVIDOR] Recebi do cliente: {mensagem}")
    janela = 5
    resposta = f"Mensagem recebida com sucesso! Janela : {janela}"
    conexao.sendall((resposta + "\n").encode("utf-8"))

    print(f"[SERVIDOR] Enviei para o cliente: {resposta}\n")
    return modo_operacao,janela


def processar_mensagem(conexao, mensagem, seqEsperado, pacotes_recebidos,janela):
    if mensagem == "END":
        print("[SERVIDOR] Recebi mensagem de fim (END).")
        return False, seqEsperado

    print(f"[SERVIDOR] Recebi pacote bruto: {mensagem}")

    resultado = extrair_pacote_data(mensagem)
    if resultado is None:
        print("[SERVIDOR] Pacote em formato inesperado.")
        return True, seqEsperado

    seq, payload,campos = resultado
    if not validar_pacote(campos):
        print("[SERVIDOR] Checksum inválido.")
        conexao.sendall(f"NACK {seqEsperado}\n".encode())
        return False, seqEsperado
        print("[SERVIDOR] Checksum inválido.")
        conexao.sendall(f"NACK {seqEsperado}\n".encode())
        return False, seqEsperado
    if seq != seqEsperado:
        conexao.sendall(f"NACK {seqEsperado}".encode())
        return False, seqEsperado

    if seq == seqEsperado:
        seqEsperado += 4

    print(f"\n[SERVIDOR] Metadados - seq={seq}, payload='{payload}'")
    pacotes_recebidos[seq] = payload

    return True, seqEsperado


def loop_recebimento(conexao, seq):
    buffer = ""
    pacotes_recebidos = {}
    handshake_recebido = False
    seqEsperado = seq
    modo_operacao = ""
    janela = 0
    continuar = False

    while True:
        data = conexao.recv(1024)

        if not data:
            return None,False,0

        buffer += data.decode("utf-8")

        
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            mensagem = linha

            if not mensagem:
                continue

            

            if not handshake_recebido:
                modo_operacao,janela = tratar_handshake(conexao, mensagem)
                handshake_recebido = True
                continue
            if modo_operacao == "GBN":
                
                continuar, seqEsperado = processar_mensagem(
                    conexao, mensagem, seqEsperado, pacotes_recebidos,janela
                )

            if seqEsperado == seq + 4*janela:
                conexao.sendall(f"ACK {seqEsperado}, Janela {random.randint(1,5)}".encode())
                return pacotes_recebidos,True,seqEsperado
            

            if not continuar:
                conexao.sendall(f"ACK END".encode())
                return pacotes_recebidos, False,seqEsperado
    
    


def main():
    servidor_socket = criar_servidor()
    conexao = aceitar_conexao(servidor_socket)
    seq = 0
    while(True):

        pacotes,continuar,seq = loop_recebimento(conexao,seq)
        if continuar == False:
            break

    conexao.close()
    servidor_socket.close()

    print("servidor encerrado")
    #exibir mensagem
    print("pacotes recebidos:", pacotes)


if __name__ == "__main__":
    main()
