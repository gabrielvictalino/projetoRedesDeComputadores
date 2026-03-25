import socket

HOST = "127.0.0.1" # localhost
PORT = 5000 # porta do servidor (pode ser qualquer porta acima de 1024)

def main():
    
    # cria o scket TCP (AF_INET = IPV4, SOCK_STREAM = TCP)
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # faz o bind: associa o socket a (HOST, PORT)
    servidor_socket.bind((HOST, PORT))
    print(f"servidor iniciado em {HOST}:{PORT}")

    # começa a escutar conexoes (1 = fila maxima de conexoes pendentes)
    servidor_socket.listen(1)
    
    # aceita uma conexao (bloqueia ate algum cliente se conectar)
    conn, addr = servidor_socket.accept()
    print(f"cliente conectado: {addr}")

    #handshake: recebe a mensagem do cliente
    data = conn.recv(1024) # buffer de 1024 bytes, lê até 1024 bytes da conexão
    mensagem = data.decode("utf-8") # decodifica os bytes para string
    print(f"[SERVIDOR] Recebi do cliente: {mensagem}")

    # responde algo para o cliente (confirmação do handshake)
    resposta = "Mensagem recebida com sucesso!"
    conn.send(resposta.encode("utf-8"))
    print(f"[SERVIDOR] Enviei para o cliente: {resposta}")

    # fecha a conexão com o cliente
    conn.close()
    servidor_socket.close()
    print("servidor encerrado")

    if __name__ == "__main__":
        main()
