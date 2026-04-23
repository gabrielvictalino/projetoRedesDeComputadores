import socket

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000  # porta do servidor

def fragmentar_texto(texto, tam_bloco=4):  # divide o texto em blocos de tamanho 4 para facilitar o envio
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def enviar_linha(sock, mensagem):
    sock.sendall((mensagem + "\n").encode("utf-8"))

def main():

    # cria socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta ao servidor
    cliente_socket.connect((HOST, PORT))
    print(f"conectado ao servidor em {HOST}:{PORT}")

    # exemplo de mensagem de handshake
    modo_operacao = "GBN"  # Go-Back-N
    tamanho_max = 100

    # formato: HANDSHAKE;modo=GBN;maxlen=100
    handshake_msg = f"HANDSHAKE;modo={modo_operacao};maxlen={tamanho_max}"
    enviar_linha(cliente_socket, handshake_msg)
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    # aguarda resposta do servidor
    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8").strip()
    print(f"[CLIENTE] Recebi do servidor: {resposta}\n")

    # leitura da mensagem do usuário
    texto = input("Digite a mensagem a ser enviada (min de 30 caracteres): ")
    if len(texto) < 30:
        print("A mensagem deve conter pelo menos 30 caracteres.")
        cliente_socket.close()
        return

    # divide o texto em blocos de até 4 caracteres (carga útil máxima)
    blocos = fragmentar_texto(texto, tam_bloco=4)
    total_pacotes = len(blocos)

    print(f"[CLIENTE] Texto será enviado em {total_pacotes} pacotes.\n")

    # envia cada bloco como um pacote de aplicação
    for seq, payload in enumerate(blocos):
        # exemplo: DATA;seq=0;total=10;payload=ABCD
        mensagem = f"DATA;seq={seq};total={total_pacotes};payload={payload}"
        enviar_linha(cliente_socket, mensagem)
        print(f"[CLIENTE] Enviei para o servidor: {mensagem}")

    # depois de todos os pacotes terem sido enviados, envia uma mensagem de fim
    enviar_linha(cliente_socket, "END")
    print(f"[CLIENTE] Enviei mensagem de fim: END")

    # fecha o socket
    cliente_socket.close()
    print("conexão encerrada")

if __name__ == "__main__":
    main()