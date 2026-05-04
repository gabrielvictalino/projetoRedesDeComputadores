import socket


HOST = "127.0.0.1"  # localhost
PORT = 5000  # porta do servidor (pode ser qualquer porta acima de 1024)


def processar_pacote_data(mensagem):
    # exemplo de mensagem: "DATA;seq=0;total=10;payload=ABCD"
    partes = mensagem.split(";")

    if partes[0] != "DATA":
        return None

    campos = {}
    for parte in partes[1:]:
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            campos[chave] = valor

    seq = int(campos.get("seq", -1))
    total = int(campos.get("total", -1))
    payload = campos.get("payload", "")
    checksum_recebido = int(campos.get("checksum", 0))
    
    soma_total = 0
    
    for caractere in payload:
        soma_total += ord(caractere)

    if soma_total != checksum_recebido:
        return False, seq, total, payload

    return True, seq, total, payload


def main():
    # cria o socket TCP (AF_INET = IPV4, SOCK_STREAM = TCP)
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # faz o bind: associa o socket a (HOST, PORT)
    servidor_socket.bind((HOST, PORT))
    print(f"servidor iniciado em {HOST}:{PORT}")

    # começa a escutar conexoes (1 = fila maxima de conexoes pendentes)
    servidor_socket.listen(1)

    # aceita uma conexao (bloqueia ate algum cliente se conectar)
    conexao, endereco = servidor_socket.accept()
    print(f"cliente conectado: {endereco}")

    # variaveis para controle da comunicação
    pacotes_recebidos = {}
    total_esperado = None
    handshake_recebido = False
    buffer = ""

    while True:
        # lê até 1024 bytes da conexão
        data = conexao.recv(1024)

        if not data:
            # conexao fechada pelo cliente
            break

        # adiciona o que chegou ao buffer
        buffer += data.decode("utf-8")

        # processa todas as mensagens completas encontradas no buffer
        # cada mensagem termina com "\n"
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            mensagem = linha

            if not mensagem:
                continue

            # handshake: a primeira mensagem recebida do cliente
            if not handshake_recebido:
                print(f"[SERVIDOR] Recebi do cliente: {mensagem}")

                # responde algo para o cliente (confirmação do handshake)
                resposta = "Mensagem recebida com sucesso!"
                conexao.sendall((resposta + "\n").encode("utf-8"))
                print(f"[SERVIDOR] Enviei para o cliente: {resposta}\n")

                handshake_recebido = True
                continue

            # verifica se recebeu a mensagem de fim
            if mensagem == "END":
                print("[SERVIDOR] Recebi mensagem de fim (END).")
                break

            print(f"[SERVIDOR] Recebi pacote bruto: {mensagem}")

            resultado = processar_pacote_data(mensagem)
            if resultado is None:
                print("[SERVIDOR] Pacote em formato inesperado.")
                continue

            checksun_correto, seq, total, payload = resultado

            if not checksun_correto:
                print("Número de digitos incorretos") # Solução temp
                break

            # guarda total de pacotes se ainda não souber
            if total_esperado is None:
                total_esperado = total
                print(f"[SERVIDOR] Total de pacotes esperado: {total_esperado}")

            # metadados do pacote
            print(f"\n[SERVIDOR] Metadados - seq={seq}, total={total}, payload='{payload}'")

            # armazena payload por número de sequência
            pacotes_recebidos[seq] = payload

        # se a mensagem END foi recebida, encerra o while principal também
        if mensagem == "END":
            break

    # remontar a mensagem completa
    if total_esperado is not None:
        mensagem_completa = ""
        faltando = []

        for i in range(total_esperado):
            # se algum seq faltar, coloca um marcador
            if i in pacotes_recebidos:
                parte = pacotes_recebidos[i]
            else:
                parte = "[FALTA PACOTE]"
                faltando.append(i)

            mensagem_completa += parte

        print(f"\n[SERVIDOR] Mensagem completa reconstruída: {mensagem_completa}")

        if faltando:
            print(f"[SERVIDOR] Pacotes faltando: {faltando}")
        else:
            print("[SERVIDOR] Nenhum pacote faltando.")
    else:
        print("[SERVIDOR] Nenhum pacote DATA recebido.")

    # fecha a conexão com o cliente
    conexao.close()
    servidor_socket.close()
    print("servidor encerrado")

if __name__ == "__main__":
    main()