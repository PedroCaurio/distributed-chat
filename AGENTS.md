# Enunciado do Trabalho
Desenvolva um chat multiusuário usando sockets, com arquitetura cliente-servidor e uso de threads. O chat deve permitir que vários usuários conversem em tempo real, com todas as mensagens passando primeiro pelo servidor, que as envia aos demais usuários. O servidor deve ter alguma forma de tolerância a falhas (exemplo: servidor secundário ativado automaticamente).

O que será avaliado?

1. Acesso via navegador (web)
O chat deve funcionar no navegador, sem instalar nada.
O servidor deve estar hospedado online (não pode ser localhost) 
Exemplos de serviços para deploy (Render, Fly.io, Railway, Glitch, Replit...)

2. Criatividade e extras
Funcionalidades a mais, como:
Interface amigável;
Identificação de usuários;
Histórico de mensagens, etc...

3. Relatório em PDF (de acordo com as orientações)

Orientações de entrega
1. Requisitos Técnicos
1.1. Funcionalidades obrigatórias:
O sistema deve permitir a comunicação simultânea entre múltiplos usuários.
O servidor deve instanciar uma thread para cada conexão com um cliente.
O cliente deve instanciar uma thread dedicada à recepção de mensagens.
A aplicação cliente deve ser acessível via navegador web:
Isso requer um servidor HTTP embutido (ex.: com Svelte, React, Flask, CherryPy, etc.).
O sistema deve possuir tolerância a falhas:
Implementar um mecanismo de replicação do servidor. Ex: um segundo processo que assume quando o principal falha.

1.2. Qualidade do código:
Todo o código deve estar organizado e devidamente comentado.
Utilizar boas práticas de programação (modularização, padronização de nomes, etc.).

2. Entrega
A entrega consiste em um arquivo compactado (.zip ou .tar.gz) submetido via AVA FURG, até a data e horário estabelecidos. O pacote deve conter:
Código-fonte completo da aplicação;
Arquivo requirements.txt (ou instruções de instalação das bibliotecas);
Arquivo README.md com instruções básicas de execução;
Relatório técnico em formato PDF.
Entregas fora do prazo ou por e-mail não serão aceitas.

3. Apresentação Presencial
A apresentação será individual, mesmo em trabalho em grupo. Um integrante será sorteado na hora.
A pessoa sorteada deverá:
Explicar o funcionamento do sistema;
Compilar e executar o projeto;
Demonstrar exemplos de uso ao vivo.

4. Relatório Técnico (PDF)
O relatório deve conter:
Identificação do(s) integrante(s);
Motivação e definição do problema;
Arquitetura do sistema e regras de funcionamento;
Guia de instalação das dependências (bibliotecas, frameworks, etc.);
Dificuldades enfrentadas e soluções adotadas;
Conclusão e lições aprendidas.

5. Regras e Observações
Linguagem de programação: livre escolha.
Tamanho do grupo: individual, em dupla ou trio.
O chat deve ter uma interface web amigável.
Plágio será punido com nota zero, e os casos serão encaminhados à Coordenadoria de Graduação.
Este trabalho é uma oportunidade para integrar conhecimentos de redes, concorrência e desenvolvimento web.

-----------
# Contexto do Projeto: Sistema de Chat Distribuído

Você é um Engenheiro de Software Sênior especialista em Python, concorrência (threads), sistemas distribuídos e React. 
Estamos desenvolvendo um trabalho acadêmico de Sistemas Distribuídos que consiste em um chat multiusuário em tempo real utilizando arquitetura cliente-servidor, sockets nativos (TCP) e tolerância a falhas.

## ⚠️ Restrições e Regras Críticas (NÃO VIOLAR)
- **Sockets Nativos:** É EXPRESSAMENTE PROIBIDO o uso de WebSockets (ex: `socket.io`, `websockets`) para a comunicação principal entre Cliente e Servidor. Utilize apenas a biblioteca nativa `socket` do Python.
- **Threads Obrigatórias:** 
  - O Servidor deve criar uma nova `thread` para cada conexão de cliente recebida.
  - O Cliente deve obrigatoriamente instanciar uma `thread` dedicada exclusivamente para o `.recv()` de mensagens.
- **Ambiente:** O código deve rodar perfeitamente em ambientes Linux.
- **Tolerância a Falhas:** O sistema backend deve garantir a continuidade do serviço caso a instância principal falhe.

---

## Arquitetura do Sistema (100% web — demonstração em aula)

### 1. Servidor unificado (Render — 2 instâncias + LB HTTP)
- **Linguagem:** Python 3 + FastAPI
- **Infraestrutura:** Duas instâncias Web Service no Render (`render.yaml`), load balancer HTTP nativo.
- **Estado:** Redis (Upstash) — histórico, sessões web, pub/sub entre instâncias.
- **Failover:** Ao cair uma instância, o navegador reconecta SSE, recupera histórico via `/history?since=` e mantém `session_id` no Redis.

### 2. Frontend (React — mesmo deploy)
- Build Vite embutido no Docker; servido na mesma URL pública.
- **Zero instalação** para alunos/professor: apenas abrir o link.

### 3. Cliente proxy (`client/` — opcional)
- Mantido para desenvolvimento e referência (thread `recv` + TCP).
- **Não usado** na apresentação 100% web.

---

## 🛠️ Stack Tecnológica
- **Servidor & Cliente Proxy:** Python (bibliotecas `socket`, `threading`, `redis`, e `FastAPI` para a ponte HTTP).
- **Frontend:** React (Vite, Axios, TailwindCSS para estilização amigável).
- **Infraestrutura:** Render (Servidor Backend), Vercel (Frontend UI), Upstash ou Redis Cloud (Redis DB).

---

## Diretrizes de Código e Boas Práticas (PEP 8)

Ao gerar, modificar ou refatorar códigos, siga ESTRITAMENTE as seguintes diretrizes:

1. **Clean Code e PEP 8:** O código Python deve ser idiomático, tipado (Type Hints) e seguir as normas PEP 8.
2. **Documentação:** 
   - O cabeçalho de cada script principal deve conter um *docstring* resumindo seu propósito.
   - Funções e métodos complexos devem possuir *docstrings* claras indicando parâmetros e retornos.
3. **Desacoplamento e Modularização:**
   - Evite *Spaghetti Code*. Separe a lógica de rede (sockets), a lógica de negócios (gerenciamento de chat) e a lógica de apresentação (HTTP/React).
   - Utilize **Decorators** para tratamento de exceções de conexão e **Wrappers** para centralizar envios e recebimentos de pacotes (ex: para serialização/desserialização JSON via sockets).
4. **Variáveis de Ambiente:** NENHUMA credencial, URL de Render, ou string de conexão do Redis deve estar hardcoded. Utilize `python-dotenv` e exija a presença de arquivos `.env`.
5. **Git Workflow:** Todo código gerado deve ser preparado pensando em um fluxo de branch separada -> Pull Request -> Merge.

---
## Manutenção Contínua de Documentação

É OBRIGATÓRIO que você (o agente) crie e mantenha documentações técnicas em arquivos `.md` separados na pasta `docs/`. 

- **Contratos e Payloads:** Crie um arquivo `docs/PAYLOADS.md` contendo a estrutura JSON exata das mensagens trafegadas nos sockets (ex: login, envio de mensagem, broadcast, erro).
- **Visão Geral da Arquitetura:** Crie um arquivo `docs/ARCHITECTURE.md` detalhando o fluxo de dados entre React -> Proxy Local -> Servidor Render -> Redis.
- **Atualização Automática (Gatilho Crítico):** Sempre que você sugerir ou implementar uma alteração no formato dos pacotes enviados via socket, nas rotas do servidor HTTP local, ou na estrutura da arquitetura, **você deve, na mesma resposta, editar e atualizar automaticamente os arquivos `.md` correspondentes.** A documentação nunca pode ficar assíncrona em relação ao código-fonte.

---
## Requisitos de Avaliação (Para Check-list)
- [ ] Acesso via navegador sem instalação (URL pública Render).
- [ ] Múltiplos usuários simultâneos.
- [ ] Identificação de usuários (Username).
- [ ] Histórico de mensagens recuperável.
- [ ] Servidor não está em localhost (Deploy no Render).
- [ ] Replicação/Tolerância a falhas implementada e descrita.
- [ ] Preparação dos scripts para o arquivo `requirements.txt` e empacotamento em `.zip` ou `.tar.gz` para entrega no AVA.