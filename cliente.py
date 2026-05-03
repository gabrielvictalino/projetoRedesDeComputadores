import socket
from threading import Timer

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000  # porta do servidor

def fragmentar_texto(texto, tam_bloco=4):  # divide o texto em blocos de tamanho 4 para facilitar o envio
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def enviar_linha(sock, mensagem):
    sock.sendall((mensagem + "\n").encode("utf-8"))

def enviar_lote(comeco_do_envio,janela,pacotes,cliente_socket):
    for i in range(comeco_do_envio,janela):
        # exemplo: DATA;seq=0;total=10;payload=ABCD

        enviar_linha(cliente_socket, pacotes[i])
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")
    resposta = esperarAckOuNack(cliente_socket,pacotes,pacotes,comeco_do_envio+janela)
    return reposta


def esperarAckOuNack(cliente_socket,pacotes,ateOndeFoiMandado,ondeComecouMandar):
    cliente_socket.settimeout(5)
    try:
        resposta = cliente_socket.recv(1024)
    except:
        retransmissao(ondeComecouMandar,pacotes,ateOndeFoiMandado,cliente_socket)

    partes = resposta.split()

    if partes[0] == "NACK":
        retransmissao(int(partes[1]),pacotes,ateOndeFoiMandado,cliente_socket)
    
    if partes[1] == "ACK":
        return f"Confirmado {ateOndeFoiMandado} "

def retransmissao(numeroNack,pacotes,ateQualPacoteEnviar,cliente_socket):
    for i in range(numeroNack,ateQualPacoteEnviar):
        enviar_linha(cliente_socket, pacotes[i])    
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")

    esperarAckOuNack(cliente_socket,pacotes,ateQualPacoteEnviar)




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
    seq=0
    for i, payload in enumerate(blocos):
        # exemplo: DATA;seq=0;total=10;payload=ABCD
        arrayPacotes[i].append(f"DATA;seq={seq};payload={payload}") 
        seq= seq+4

    loteEnviado = False
    comeco_envio = 0
    tamanhoJaEnviado = 0
    janela = 5
    while not loteEnviado:
        resposta = enviar_lote(comeco_do_envio,janela,pacotes,cliente_socket)
        partes = resposta.split()
        comeco_envio = int(partes[1])
        tamanhoJaEnviado += janela


    
    
    
    # print(f"[CLIENTE] Enviei para o servidor: {mensagem}")
    # enviar_linha(cliente_socket, mensagem)

    # depois de todos os pacotes terem sido enviados, envia uma mensagem de fim
    enviar_linha(cliente_socket, "END")
    print(f"[CLIENTE] Enviei mensagem de fim: END")

    # fecha o socket
    cliente_socket.close()
    print("conexão encerrada")

if __name__ == "__main__":
    main()


