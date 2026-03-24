import socket

HOST = "127.0.0.1"  # localhost
PORT = 5000  # porta do servidor (pode ser qualquer porta acima de 1024)

def main():
    # cria o scket TCP (AF_INET = IPV4, SOCK_STREAM = TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # faz o bind: associa o socket a (HOST, PORT)
    server_socket.bind((HOST, PORT))
    print(f"Servidor escutando em {HOST}:{PORT}...")

    # começa a escutar conexoes (1 = fila maxima de conexoes pendentes)
    server_socket.listen(1)

    # aceita uma conexao (bloqueia ate algum cliente se conectar)
    conn, addr = server_socket.accept()
    print(f"Conexão estabelecida com {addr}")

    # === Handshake simples: receber mensagem inicial do cliente ===
    data = conn.recv(1024) # lê até 1024 bytes da conexão
    mensagem = data.decode("utf-8") # decodifica bytes para string
    print(f"[SERVIDOR] Recebi do cliente: {mensagem}")

    # Responde algo para o cliente (confirmação do handshake)
    resposta = "HANDSHAKE_OK_SERVIDOR"
    conn.sendall(resposta.encode("utf-8"))
    print(f"[SERVIDOR] Enviei para o cliente: {resposta}")

    # Fecha a conexão com o cliente
    conn.close()
    server_socket.close()
    print("Servidor encerrado.")

if __name__ == "__main__":
    main()
