# Client Side

Interface web do DS Chat (Distributed Systems Chat). Este módulo foi construido com React,
TypeScript e Vite.

## Principais Tecnologias

- React 19
- TypeScript
- Vite
- lucide-react para ícones

## Funcionalidades

- Tela de identificação do usuário.
- Lista de conversas com busca local.
- Botão para derrubar uma instância do servidor e verificar a transparência do mesmo.
- Ações de criar conversa e enviar mensagem, com outros usuários

## Requisitos

- Node.js instalado.
- npm instalado.

## Instalação

```bash
npm install
```

## Rodar Localmente

```bash
npm run dev
```

## Estrutura

```text
client/
|-- src/
|   |-- components/
|   |-- data/
|   |-- services/
|   |-- App.tsx
|   |-- main.tsx
|   |-- styles.css
|   `-- types.ts
|-- index.html
|-- package.json
|-- tsconfig.json
-- vite.config.ts
```

## TODO

As chamadas de backend ficam concentradas em `src/services/chatService.ts`.
Atualmente, essas funcoes lancam erros de `TODO backend`, que sao exibidos na
interface como avisos de funcionalidade aguardando implementacao.

Quando o servidor estiver disponivel, esse arquivo deve ser atualizado para
chamar as rotas reais do backend.