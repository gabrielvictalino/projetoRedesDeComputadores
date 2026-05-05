
# Projeto de Infraestrutura de Comunicação

# Descrição

Este projeto implementa uma infraestrutura de comunicação entre um cliente e um servidor utilizando sockets TCP/IP em Python. O objetivo é demonstrar, de forma prática, os conceitos fundamentais de programação de redes, incluindo controle de erro, controle de fluxo e protocolos de transmissão confiável.

# Arquitetura

O projeto segue o modelo cliente-servidor com duas aplicações principais:

* Servidor (servidor.py): Aguarda conexões na porta 5000 (localhost), processa o handshake, recebe pacotes de dados, valida integridade e sequência, e responde com ACKs ou NACKs conforme o protocolo utilizado.
* Cliente (cliente.py): Conecta-se ao servidor, realiza o handshake negociando o modo de operação, fragmenta a mensagem em pacotes e realiza o envio utilizando os protocolos Go-Back-N ou Repetição Seletiva.

# Funcionalidades

# Handshake

O cliente inicia a comunicação com um handshake contendo:

* Modo de operação: Go-Back-N (GBN) ou Repetição Seletiva (RS)

Formato da mensagem:

HANDSHAKE;modo=GBN

O servidor responde informando o tamanho da janela de transmissão:

Mensagem recebida com sucesso! Janela : 5

# Comunicação

* Estabelecimento de conexão TCP entre cliente e servidor
* Fragmentação da mensagem em blocos menores
* Envio de pacotes com controle de sequência
* Verificação de integridade com checksum
* Uso de ACK e NACK para controle de erros
* Encerramento da conexão com mensagem END

# Fragmentação de Dados

A mensagem digitada pelo usuário é dividida em blocos de até 4 caracteres, formando múltiplos pacotes para envio.

Estrutura dos Pacotes

Os pacotes seguem o formato:

DATA;seq=0;payload=ABCD;checksum=123

Onde:

* seq representa o número de sequência (incrementado de 4 em 4)
* payload contém os dados
* checksum garante a integridade da informação

# Verificação de Integridade

O checksum é calculado com base na soma dos caracteres do payload:

sum(ord(c) for c in payload) % 256

Se houver erro:

* O servidor envia um NACK
* O cliente realiza retransmissão

# Protocolos Implementados

Go-Back-N (GBN)

* Envio de pacotes em janelas
* ACK confirma todos os pacotes até um determinado ponto
* Em caso de erro, a janela inteira é retransmitida

Repetição Seletiva (RS)

* Pacotes são confirmados individualmente
* O cliente mantém controle dos pacotes confirmados
* Apenas pacotes não confirmados são reenviados

# Tecnologias Utilizadas

* Python
* Socket API (biblioteca padrão)
* IPv4 (AF_INET)
* TCP (SOCK_STREAM)

Como Executar

1. Iniciar o Servidor

python servidor.py

Output esperado:

servidor iniciado em 127.0.0.1:5000

2. Executar o Cliente (abrir outro terminal)

python cliente.py

Durante a execução, será solicitado o modo de operação:

Digite o modo de operação a ser trabalhado: (GBN)/(RS)

Output esperado:

conectado ao servidor em 127.0.0.1:5000
[CLIENTE] Enviei para o servidor: HANDSHAKE;modo=GBN
[CLIENTE] Recebi do servidor: Mensagem recebida com sucesso! Janela : 5

Estrutura do Projeto

projetoRedesDeComputadores/
├── cliente.py        # Cliente TCP/IP
├── servidor.py       # Servidor TCP/IP
└── README.md         # Este arquivo

Conceitos de Redes Implementados

* Socket: Interface para comunicação em rede
* Bind: Associação de um socket a um endereço IP e porta
* Listen/Accept: Servidor aguardando e aceitando conexões
* Handshake: Negociação inicial entre cliente e servidor
* Codificação UTF-8: Conversão entre caracteres e bytes
* Controle de fluxo: Uso de janelas deslizantes
* Controle de erro: Uso de checksum, ACK e NACK
* Go-Back-N (GBN): Protocolo de retransmissão por janela
* Repetição Seletiva (RS): Retransmissão apenas de pacotes perdidos

Limitações

* Comunicação restrita ao localhost
* Apenas um cliente por vez
* Tamanho fixo de payload (4 caracteres)
* Não há simulação explícita de perda de pacotes na rede

Relatório de uso de IA

Relatório de uso de IA

Entrega 1

O uso da Inteligência Artificial neste projeto foi restrito ao apoio teórico, sendo utilizado apenas para:

* Pesquisa sobre a biblioteca socket
* Compreensão de conceitos de redes de computadores

Etapa final do projeto

Na etapa final do desenvolvimento, a IA também foi utilizada de forma pontual para:

* Auxiliar na identificação e correção de erros no código
* Esclarecer dúvidas sobre comportamentos inesperados na comunicação cliente-servidor
