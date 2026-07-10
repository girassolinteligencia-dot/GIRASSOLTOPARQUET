# Serviço de Webhook para Emissão de Licenças - GIRASSOLtoPARQUET

Serviço construído em FastAPI para recepção de webhooks de vendas da Hotmart, geração automática de licenças assinadas digitalmente e entrega automatizada aos clientes via SMTP.

---

## 🛠️ Execução Local para Desenvolvimento

### 1. Preparação

Certifique-se de ter executado a geração do par de chaves mestre na raiz do projeto:

```bash
.venv\Scripts\python.exe scripts/gerar_chaves_mestre.py
```

### 2. Configurar Variáveis de Ambiente

Crie o arquivo `licensing_service/.env` baseado no modelo [licensing_service/.env.example](file:///c:/GIRASSOLTOPARQUET/parquet-converter/licensing_service/.env.example):

```env
HOTMART_HOTTOK=token_da_hotmart_aqui
SMTP_HOST=smtp.exemplo.com
SMTP_PORT=587
SMTP_USER=usuario@exemplo.com
SMTP_PASSWORD=senha_secreta
EMAIL_REMETENTE=licencas@girassolinteligencia.com.br
```

### 3. Instalar Dependências e Executar

Ative o ambiente virtual e instale as dependências de desenvolvimento ou de serviço:

```bash
.venv\Scripts\pip.exe install -r licensing_service/requirements.txt
```

Inicie o servidor com uvicorn:

```bash
.venv\Scripts\uvicorn.exe licensing_service.main:app --reload --host 127.0.0.1 --port 8000
```

O endpoint estará disponível em `http://127.0.0.1:8000/webhook/hotmart`.

---

## 🐳 Deploy em Produção (via Docker)

O serviço de webhook pode ser contêinerizado e executado em qualquer servidor compatível com Docker:

### 1. Compilação da Imagem Docker

Na raiz do projeto (`parquet-converter`), construa a imagem:

```bash
docker build -t girassol-licensing-service -f licensing_service/Dockerfile .
```

### 2. Executar Container

Inicie o container repassando as variáveis de ambiente necessárias ou referenciando um arquivo `.env` seguro no servidor:

```bash
docker run -d \
  --name girassol-licensing \
  --restart always \
  -p 8000:8000 \
  --env-file /caminho/seguro/no/servidor/.env \
  -v /var/lib/girassol-licensing/scripts:/app/scripts \
  -v /var/lib/girassol-licensing/keys:/app/keys \
  girassol-licensing-service
```

> [!NOTE]
> Mapear o diretório de `/app/scripts` garante a persistência física do arquivo de registros SQLite `registro_licencas.db`. Mapear `/app/keys` garante que a chave privada gerada permaneça persistente.

### 3. Configuração do Reverse Proxy Nginx (com HTTPS)

Como a Hotmart exige entrega por protocolo seguro (HTTPS), configure um bloco do Nginx no VPS apontando para o container Docker (ou interface de rede Tailscale):

```nginx
server {
    listen 80;
    server_name licencas.girassolinteligencia.com.br;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name licencas.girassolinteligencia.com.br;

    ssl_certificate /etc/letsencrypt/live/licencas.girassolinteligencia.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/licencas.girassolinteligencia.com.br/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Obtenha o certificado SSL gratuito via Let's Encrypt / Certbot:

```bash
sudo certbot --nginx -d licencas.girassolinteligencia.com.br
```

---

## 🪵 Auditoria e Logs

Todas as requisições, eventos processados, idempotência e falhas de envio são gravados no arquivo:

* `licensing_service/logs/webhook.log` (ou no stdout/docker logs do container).
