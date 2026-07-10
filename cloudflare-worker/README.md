# Cloudflare Worker de Licenciamento - GIRASSOLtoPARQUET

Serviço serverless integrado à Hotmart para emissão e entrega de licenças offline assinadas digitalmente.

---

## 🛠️ Comandos de Configuração Manual (Segredos)

As credenciais sensíveis e segredos nunca são armazenados em arquivos. Devem ser registrados de forma segura usando o Cloudflare Secrets.

Execute os seguintes comandos no terminal na pasta `cloudflare-worker/`:

### 1. Definir Token de Autenticação da Hotmart

Este token é configurado no painel da Hotmart e enviado no cabeçalho `X-HOTMART-HOTTOK`.

```bash
npx wrangler secret put HOTMART_HOTTOK
```

Nota: Digite o token cadastrado na Hotmart quando solicitado pelo terminal.

### 2. Definir a Chave Privada do Emissor (Criptografia)

É o conteúdo completo do arquivo local `keys/private_key.pem` (incluindo os cabeçalhos `-----BEGIN PRIVATE KEY-----` e `-----END PRIVATE KEY-----`).

```bash
npx wrangler secret put LICENSE_PRIVATE_KEY
```

Nota: Cole o conteúdo completo do seu arquivo `keys/private_key.pem` local quando for solicitado pelo terminal.

### 3. Definir a Chave de API do Resend.com (E-mails)

Obtenha a chave de API gratuita no painel do Resend.com.

```bash
npx wrangler secret put RESEND_API_KEY
```

Nota: Digite a chave de API (API Key) obtida do Resend quando solicitado.

### 4. Definir o E-mail Remetente (Opcional)

Define o e-mail de envio das licenças. Deve ser um domínio verificado no Resend.

```bash
npx wrangler secret put EMAIL_REMETENTE
```

Exemplo de valor a ser inserido: `licencas@girassolinteligencia.com.br`

---

## 🚀 Como Realizar o Deploy

Após configurar as secrets acima e ter o `wrangler login` autenticado:

### 1. Instalar Dependências do Wrangler (se necessário)

```bash
npm install -g wrangler
```

Nota: Se preferir não instalar globalmente, você pode executar o CLI do wrangler usando o prefixo `npx wrangler`.

### 2. Executar Deploy

Execute o comando de publicação na pasta do Worker:

```bash
npx wrangler deploy
```

O Cloudflare gerará uma URL pública para o Worker, por exemplo:
`https://girassol-licensing-worker.<seu-usuario>.workers.dev`

### 3. Configurar Webhook no Painel da Hotmart

1. Acesse o painel da Hotmart -> Ferramentas -> Webhook (API e Integrações).
2. Adicione uma nova configuração de envio.
3. Insira a URL do Worker apontando para o endpoint do webhook:
   `https://girassol-licensing-worker.<seu-usuario>.workers.dev/webhook/hotmart`
4. Selecione os eventos:
   * **Compra Aprovada**
   * **Compra Cancelada**
   * **Reembolso**
5. Em configurações de cabeçalho, certifique-se de que o **Token (HOTTOK)** coincide com o cadastrado no segredo `HOTMART_HOTTOK`.

---

## 🪵 Visualizar Logs de Produção

Para depurar requisições em tempo real no Worker de produção, execute:

```bash
npx wrangler tail
```
