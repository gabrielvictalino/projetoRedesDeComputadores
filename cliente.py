import socket

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000         # mesma porta do servidor

def main():
    # Cria o socket TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conecta ao servidor
    client_socket.connect((HOST, PORT))
    print(f"Conectado ao servidor em {HOST}:{PORT}")

    # === Handshake simples: enviar mensagem inicial ===
    # Exemplo de mensagem com modo de operação e tamanho máximo
    modo_operacao = "GBN"     # Go-Back-N (por enquanto só texto)
    tamanho_maximo = 100      # exemplo qualquer

    handshake_msg = f"HANDSHAKE;modo={modo_operacao};maxlen={tamanho_maximo}"
    client_socket.sendall(handshake_msg.encode("utf-8"))
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    # Espera a resposta do servidor
    data = client_socket.recv(1024)
    resposta = data.decode("utf-8")
    print(f"[CLIENTE] Recebi do servidor: {resposta}")

    # Fecha o socket
    client_socket.close()
    print("Cliente encerrado.")

if __name__ == "__main__":
    main()
