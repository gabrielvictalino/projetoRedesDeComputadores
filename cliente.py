import socket

HOST = "127.0.0.1" # endereço do servidor (localhost)
PORT = 5000 # porta do servidor

def main():

    # cria socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta ao servidor
    cliente_socket.connect((HOST, PORT))
    print(f"conectado ao servidor em {HOST}:{PORT}")

    # == handshake ==
    # exemplo de mensagem de handshake
    modo_operacao = "GBN"
    tamanho_max = 100

    handshake_msg = f"HANDSHAKE;modo={modo_operacao};maxlen={tamanho_max}"
    cliente_socket.sendall(handshake_msg.encode("utf-8"))
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    # aguarda resposta do servidor
    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8")
    print(f"[CLIENTE] Recebi do servidor: {resposta}")

    # fecha o socket
    cliente_socket.close()
    print("conexão encerrada")

if __name__ == "__main__":
    main()