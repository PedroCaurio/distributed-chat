# Enunciado do Trabalho
Desenvolva um chat multiusuário usando sockets, com arquitetura cliente-servidor e uso de threads. O chat deve permitir que vários usuários conversem em tempo real, com todas as mensagens passando primeiro pelo servidor, que as envia aos demais usuários. O servidor deve ter alguma forma de tolerância a falhas (exemplo: servidor secundário ativado automaticamente).

O que será avaliado?

1. Acesso via navegador (web)
O chat deve funcionar no navegador, sem instalar nada.
O servidor deve estar hospedado online (não pode ser localhost)
Exemplos de serviços para deploy (Fly.io, Railway, Glitch, Replit...)

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

Chat multiusuário em tempo real com **arquitetura 100% web** (Fly.io + Upstash), sockets TCP opcionais e tolerância a falhas.

## Restrições críticas
- **Sockets nativos** para camada TCP (sem `socket.io` / WebSockets no protocolo principal).
- **Threads:** servidor com thread por conexão TCP; pub/sub em thread dedicada; SSE com recepção bloqueante por cliente web.
- **Sem credenciais hardcoded** — use `.env` / Fly secrets.
- **Tolerância a falhas:** 2 instâncias Fly + Redis + reconexão SSE.

## Arquitetura (produção)

### Fly.io + Docker unificado
- `Dockerfile` na raiz: build React + API FastAPI.
- `fly scale count 2` — load balancer HTTP.
- Upstash Redis — histórico, sessões, pub/sub.

### Front-end
- React em `frontend/`; servido na **mesma URL** do app (`https://*.fly.dev`).
- **Zero instalação** na demonstração.

### Legado
- `legacy/client/` — proxy TCP+HTTP local (relatório / dev); **não** usado em produção.

## Stack
- **Python:** FastAPI, redis, threading, socket (opcional)
- **Front:** React, Vite
- **Infra:** Fly.io, Upstash

## Documentação (manter sincronizada)
- `docs/ARCHITECTURE.md` — fluxo Navegador → Fly → Redis
- `docs/PAYLOADS.md` — contratos HTTP (+ TCP legado)
- `docs/DEPLOY.md` — deploy Fly.io

## Checklist de avaliação
- [ ] URL pública Fly (sem instalar nada)
- [ ] Múltiplos usuários
- [ ] Username + histórico
- [ ] 2 instâncias + failover demonstrável
- [ ] `requirements.txt` + README + relatório PDF
