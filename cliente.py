import socket
from threading import Timer

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000  # porta do servidor

def fragmentar_texto(texto, tam_bloco=4):  # divide o texto em blocos de tamanho 4 para facilitar o envio
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def enviar_linha(sock, mensagem):
    sock.sendall((mensagem + "\n").encode("utf-8"))

def enviar_lote(cliente_socket, pacotes, comeco_do_envio, ultimo_bite, janela):
    if comeco_do_envio + janela <= ultimo_bite:
        fim_do_envio = comeco_do_envio + janela
    
    else:
        fim_do_envio = ultimo_bite

    for i in range(comeco_do_envio, fim_do_envio):
        # exemplo: DATA;seq=0;total=10;payload=ABCD

        enviar_linha(cliente_socket, pacotes[i])
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")
    resposta = esperarAckOuNack(cliente_socket,pacotes,comeco_do_envio, fim_do_envio)
    return resposta

def calcular_checksum(payload):
    soma_total = 0
    
    for caractere in payload:
        soma_total += ord(caractere)

        # Ord transforma o caractere em um valor numerico de utf-8
        
    return soma_total

def esperarAckOuNack(cliente_socket,pacotes,comeco_do_envio,fim_do_envio):
    cliente_socket.settimeout(5)
    try:
        dados = cliente_socket.recv(1024)
        resposta = dados.decode("utf-8").strip()
    except:
        return retransmissao(cliente_socket,pacotes,comeco_do_envio,fim_do_envio)

    partes = resposta.split()
    tipo = partes[0]
    numero = partes[1]

    if tipo == "NACK":
        return retransmissao(cliente_socket, pacotes, int(numero), fim_do_envio)
    
    if tipo == "ACK":
        return (f"ACK {numero}")
    
    return retransmissao(cliente_socket, pacotes, comeco_do_envio, fim_do_envio)

def retransmissao(cliente_socket, pacotes, comeco_do_envio, fim_do_envio):
    print(f"[CLIENTE] Reenviando do pacote {comeco_do_envio} até {fim_do_envio - 1}")
    for i in range(comeco_do_envio ,fim_do_envio):
        enviar_linha(cliente_socket, pacotes[i])    
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")

    return esperarAckOuNack(cliente_socket, pacotes, comeco_do_envio, fim_do_envio)



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

    arrPacotes = []
    for i, payload in enumerate(blocos):
        cs = calcular_checksum(payload)
        # exemplo: DATA;seq=0;total=10;payload=ABCD
        arrPacotes.append(f"DATA;seq={i};payload={payload};checksum={cs}")

    comeco_envio = 0
    janela = 5
    bites_totais = len(arrPacotes)
    while comeco_envio < bites_totais:

        resposta = enviar_lote(cliente_socket, arrPacotes, comeco_envio, bites_totais, janela)
        partes = resposta.split()

        if partes[0] == "ACK":
            comeco_envio = int(partes[1])
            print(f"Lote enviado com sucesso")
        
        else:
            print("Erro na aplicação")
    
    

    # depois de todos os pacotes terem sido enviados, envia uma mensagem de fim
    enviar_linha(cliente_socket, "END")
    print(f"[CLIENTE] Enviei mensagem de fim: END")

    # fecha o socket
    cliente_socket.close()
    print("conexão encerrada")

if __name__ == "__main__":
    main()


