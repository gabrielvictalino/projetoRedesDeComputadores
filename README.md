# Projeto de Redes de Computadores

## Descrição

Este projeto implementa uma aplicação cliente-servidor em Python que demonstra protocolos de controle de erro para transferência confiável de dados sobre TCP/IP. São implementados dois protocolos principais: Go-Back-N (GBN) e Repetição Seletiva (Repetição Seletiva - RS). O sistema inclui fragmentação de mensagens, cálculo de checksum para detecção de erros, controle de fluxo com janelas deslizantes e retransmissão automática de pacotes perdidos ou corrompidos.

## Arquitetura

O projeto segue o modelo cliente-servidor:

- **Servidor** (`servidor.py`): Aguarda conexões na porta 5000 (localhost), processa handshakes, recebe pacotes de dados e confirma recebimentos usando ACK/NACK.
- **Cliente** (`cliente.py`): Conecta ao servidor, envia handshake com modo de operação, fragmenta mensagens em pacotes e gerencia retransmissões conforme o protocolo escolhido.

## Funcionalidades

### Handshake

O cliente inicia a comunicação enviando:

- **Modo de operação**: "GBN" (Go-Back-N) ou "RS" (Repetição Seletiva)
- Formato: `HANDSHAKE;modo=<modo>`

O servidor responde confirmando o modo e definindo o tamanho da janela (ex.: "Mensagem recebida com sucesso! Janela : 5").

### Formato de Pacotes

Pacotes de dados seguem o formato:

```
DATA;seq=<sequencia>;payload=<dados>;checksum=<valor>
```

- **seq**: Número de sequência (incrementa de 4 em 4)
- **payload**: Dados (até 4 caracteres por pacote)
- **checksum**: Soma dos códigos ASCII dos caracteres do payload módulo 256

### Protocolos Implementados

#### Go-Back-N (GBN)

- Transmite janelas completas de pacotes
- Retransmite toda a janela em caso de erro ou timeout
- Confirmação cumulativa com ACKs

#### Repetição Seletiva (RS)

- Transmite pacotes individuais dentro da janela
- Retransmite apenas pacotes não confirmados
- Confirmação individual com ACKs por pacote

### Controle de Erro

- **Checksum**: Validação de integridade dos dados
- **NACK**: Solicitação de retransmissão para pacotes inválidos ou fora de sequência
- **Timeout**: Retransmissão automática após 5 segundos sem resposta

### Algoritmos 

- **Checagem de integridade (CRC-8)**: para detectar erros de transmissão
- **Criptografia simétrica (Cifra de César)**: para simular erros intencionais

## Tecnologias Utilizadas

- **Python 3**
- **Socket API** para comunicação TCP/IP
- **Threading** (no cliente para timeouts)

## Como Executar

### Pré-requisitos

- Python 3 instalado

### 1. Iniciar o Servidor

Abra um terminal e execute:

```
python servidor.py
```

Output esperado:

```
servidor iniciado em 127.0.0.1:5000
```

### 2. Executar o Cliente

Abra outro terminal e execute:

```
python cliente.py
```

O cliente solicitará:

- Modo de operação: "GBN" ou "RS"
- Mensagem a enviar (mínimo 30 caracteres)

### Exemplo de Execução

1. Inicie o servidor
2. Execute o cliente
3. Escolha o modo (ex.: GBN)
4. Digite uma mensagem longa (mínimo 30 caracteres)
5. Observe os logs de transmissão e confirmações

## Considerações Técnicas

- Porta padrão: 5000 (localhost)
- Tamanho máximo do payload: 4 caracteres por pacote
- Janela padrão: 5 pacotes (com variação possível durante a comunicação)
- Timeout: 5 segundos para ACKs
- Checksum: Soma ASCII módulo 256

## Estrutura do Projeto

```
projetoRedesDeComputadores/
├── cliente.py        # Implementação do cliente
├── servidor.py       # Implementação do servidor
└── README.md         # Este arquivo
```

## Conceitos de Redes Implementados

- **Socket**: Interface para comunicação em rede
- **Bind**: Associação de um socket a um endereço IP e porta
- **Listen/Accept**: Servidor aguardando e aceitando conexões
- **Handshake**: (aperto de mãos) Negociação de parâmetros entre cliente e servidor
- **Codificação UTF-8**: Conversão entre caracteres e bytes
- **Go-Back-N (GBN)**: Protocolo de controle de fluxo para transmissão confiável
- **Repetição Seletiva (RS)**: Protocolo de controle de fluxo para transmissão confiável com retransmissão seletiva
- **Checksum**: Soma de verificação
- **ACK/NACK**: Confirmação de recebimento ou solicitação de retransmissão
- **CRC-8**: Algoritmo de detecção de erros
- **Cifra de César**: Técnica de criptografia simples para simular erros

## Relatório de uso de IA

### Entrega 1

O uso da IA foi restrito somente a pesquisas sobre a biblioteca "socket", sendo essa indispensável para o desenvolvimento da aplicação. 
Usamos a IA para formatar, organizar e estruturar o README.

### Entrega 2

Utilizamos a IA para:

1. debuggar
2. entender conceitos relacionados ao conteúdo exposto em sala e como aplicá-los no projeto
3. estruturação e organização de código
4. formatar, organizar e estruturar o README

### Entrega 3

Utilizamos a IA para:
1. debuggar
2. entender conceitos relacionados ao conteúdo exposto em sala e como aplicá-los no projeto
3. estruturação e organização de código
4. formatar, organizar e estruturar o README
