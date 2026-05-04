import socket
from threading import Timer

HOST = "127.0.0.1"  # endereço do servidor (localhost)
PORT = 5000  # porta do servidor

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


def fragmentar_texto(texto, tam_bloco=4):  # divide o texto em blocos de tamanho 4 para facilitar o envio
    return [texto[i:i+tam_bloco] for i in range(0, len(texto), tam_bloco)]

def enviar_linha(sock, mensagem
                 ):
    sock.sendall((mensagem + "\n").encode("utf-8"))

def enviar_lote(comeco_do_envio,janela,pacotes,cliente_socket):
    for i in range(comeco_do_envio, min(comeco_do_envio + janela, len(pacotes))):
        # exemplo: "DATA;seq={seq};payload={payload}"

        enviar_linha(cliente_socket, pacotes[i])
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")
    resposta = esperarAckOuNack_gbn(cliente_socket,pacotes,comeco_do_envio+janela,comeco_do_envio)
    return resposta


def esperarAckOuNack_gbn(cliente_socket,pacotes,ateOndeFoiMandado,ondeComecouMandar):
    cliente_socket.settimeout(5)
    try:
        resposta = cliente_socket.recv(1024).decode("utf-8").strip()
        print(f"[CLIENTE] Recebi do cliente : {resposta}")
    except socket.timeout:
        return retransmissao_gbn(ondeComecouMandar,pacotes,ateOndeFoiMandado,ondeComecouMandar,cliente_socket)

    partes = resposta.split(",")
    partes1 = partes[0].split()
    partes2 = partes[1].split()

    if partes1[0] == "NACK":
        return retransmissao_gbn(int(partes1[1]),pacotes,ateOndeFoiMandado,ondeComecouMandar, cliente_socket)
    
    if partes1[0] == "ACK":
        return f"Confirmado {ateOndeFoiMandado} , Janela {partes2[1]}"

def retransmissao_gbn(numeroNack,pacotes,ateQualPacoteEnviar,ondeComecouMandar,cliente_socket):
    for i in range(numeroNack//4,ateQualPacoteEnviar):
        enviar_linha(cliente_socket, pacotes[i])    
        print(f"[CLIENTE] Enviei para o servidor: {pacotes[i]}")

    return esperarAckOuNack_gbn(cliente_socket,pacotes,ateQualPacoteEnviar,ondeComecouMandar)



    

def main():

    # cria socket TCP/IP
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta ao servidor
    cliente_socket.connect((HOST, PORT))
    print(f"conectado ao servidor em {HOST}:{PORT}")

    # exemplo de mensagem de handshake
    modo_operacao = input("Digite o modo de operação a ser trabalhado: (GBN)/(RS) ")  # Go-Back-N  ou repetição seletiva.
    tamanho_max = 100

    # formato: HANDSHAKE;modo=GBN;maxlen=100
    handshake_msg = f"HANDSHAKE;modo={modo_operacao}"
    enviar_linha(cliente_socket, handshake_msg)
    print(f"[CLIENTE] Enviei para o servidor: {handshake_msg}")

    # aguarda resposta do servidor
    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8").strip()
    resposta_separada = resposta.split("!")
    respostaSeparadaJanela = resposta_separada[1].split(":")
    respostaSeparadaJanela = respostaSeparadaJanela[1]

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
        arrPacotes.append(montar_pacote(seq,payload)) 
        seq= seq+4

    totalmenteConfirmado = False
    comeco_envio = 0
    tamanhoJaEnviado = 0
    janela = int(respostaSeparadaJanela)
    
    # comeco_envio vai dizer a partir de qual pacote eu tenho que enviar.
    #Terá incialmente valor = 0 e posteriormente terá o valor do ack recebido na resposta.
    while not totalmenteConfirmado:
        resposta = enviar_lote(comeco_envio,janela,arrPacotes,cliente_socket)
        partes = resposta.split()   
        if partes[0] == "Confirmado":
            comeco_envio = int(partes[1])//4
            tamanhoJaEnviado += comeco_envio
        if tamanhoJaEnviado>=len(arrPacotes):
            totalmenteConfirmado = True

        

    
    
    
    # print(f"[CLIENTE] Enviei para o servidor: {mensagem}")
    # enviar_linha(cliente_socket, mensagem)

    # depois de todos os pacotes terem sido enviados, envia uma mensagem de fim
    enviar_linha(cliente_socket, "END")
    print(f"[CLIENTE] Enviei mensagem de fim: END")
    data = cliente_socket.recv(1024)
    resposta = data.decode("utf-8").strip()
    print(f"[CLIENTE] Recebi a mensagem do servidor: {resposta}")
    resposta = resposta.split()

    # fecha o socket
    if(resposta[1] == "END"):
        cliente_socket.close()
        print("conexão encerrada")

if __name__ == "__main__":
    main()


