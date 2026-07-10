import os
import sys
import json
import logging
import datetime
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Garantir que a pasta scripts esteja no sys.path para importarmos licensing_core
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.licensing_core import (
    obter_caminho_db, registrar_licenca, revogar_licenca,
    buscar_licenca_por_transaction_id, gerar_licenca
)

# Configurar diretório de logs
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_filepath = os.path.join(log_dir, "webhook.log")

# Configurar logger dedicado para o Webhook
webhook_logger = logging.getLogger("webhook_audit")
webhook_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
webhook_logger.addHandler(file_handler)

# Adicionar também saída padrão para facilitar visualização no Docker/VPS
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
webhook_logger.addHandler(console_handler)

app = FastAPI(title="Serviço de Licenciamento GIRASSOLtoPARQUET")

def enviar_email_licenca(email_destino: str, lic_bytes: bytes, transaction_id: str):
    """Envia a licença gerada em anexo ao e-mail do cliente usando SMTP."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    email_remetente = os.getenv("EMAIL_REMETENTE")
    
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, email_remetente]):
        webhook_logger.error(f"Erro no envio de e-mail para {email_destino}: Variáveis de ambiente SMTP não configuradas.")
        raise ValueError("Configuração SMTP incompleta no servidor.")
        
    try:
        # Criar mensagem do e-mail
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = email_destino
        msg['Subject'] = "Sua Licença do GIRASSOLtoPARQUET"
        
        body = f"""Olá,

Agradecemos sua compra! Sua licença de uso do GIRASSOLtoPARQUET foi gerada com sucesso.

Transação: {transaction_id}

Para ativar o aplicativo:
1. Abra o Conversor Parquet Offline.
2. Na tela de ativação, clique em "Selecionar Arquivo..." e escolha o arquivo "license.lic" em anexo.
3. Clique em "Ativar Aplicativo" para começar a usar.

Se tiver qualquer problema na ativação, entre em contato conosco respondendo a este e-mail.

Atenciosamente,
Equipe Girassol Inteligência
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Anexar licença
        part = MIMEBase('application', "octet-stream")
        part.set_payload(lic_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="license.lic"')
        msg.attach(part)
        
        # Conectar e enviar
        port = int(smtp_port)
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port)
        else:
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
            
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_remetente, email_destino, msg.as_string())
        server.quit()
        
        webhook_logger.info(f"E-mail enviado com sucesso para {email_destino} (Transação: {transaction_id})")
        
    except Exception as e:
        webhook_logger.error(f"Falha ao enviar e-mail para {email_destino}: {str(e)}")
        raise e

@app.post("/webhook/hotmart")
async def hotmart_webhook(
    request: Request,
    x_hotmart_hottok: str = Header(None, alias="X-HOTMART-HOTTOK")
):
    """Recebe e processa eventos de compra da Hotmart."""
    # 1. Validar HOTTOK
    token_esperado = os.getenv("HOTMART_HOTTOK")
    if not token_esperado or x_hotmart_hottok != token_esperado:
        webhook_logger.warning("Tentativa de requisição de webhook com token inválido.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token X-HOTMART-HOTTOK inválido ou ausente."
        )
        
    try:
        payload_data = await request.json()
    except Exception as e:
        webhook_logger.error(f"Erro ao ler JSON da requisição: {str(e)}")
        raise HTTPException(status_code=400, detail="Formato JSON inválido.")
        
    event = payload_data.get("event")
    
    # Normalizar o evento para maiúsculas
    if event:
        event = event.upper()
        
    # Extrair campos da transação de forma robusta
    email = payload_data.get("data", {}).get("buyer", {}).get("email") or payload_data.get("email")
    transaction_id = payload_data.get("data", {}).get("purchase", {}).get("transaction") or payload_data.get("transaction_id") or payload_data.get("transaction")
    
    if not transaction_id:
        webhook_logger.warning(f"Evento {event} ignorado porque não contém transaction_id.")
        return {"status": "ignored", "reason": "missing_transaction_id"}
        
    db_path = obter_caminho_db()
    
    # 2. Processar de acordo com o tipo de evento
    if event == "PURCHASE_APPROVED":
        if not email:
            webhook_logger.error(f"Transação {transaction_id} falhou: E-mail do comprador não encontrado no payload.")
            raise HTTPException(status_code=400, detail="E-mail do comprador ausente.")
            
        # Checar idempotência
        licenca_existente = buscar_licenca_por_transaction_id(db_path, transaction_id)
        if licenca_existente:
            webhook_logger.info(f"Transação {transaction_id} já processada anteriormente (idempotência). Retornando 200.")
            return {"status": "ignored", "reason": "already_processed", "transaction_id": transaction_id}
            
        # Gerar licença
        try:
            lic_bytes = gerar_licenca(
                email=email,
                hardware_id=None,
                validade=None,
                tipo="perpetua"
            )
            
            # Registrar no banco local
            sha256_hash = hashlib.sha256(lic_bytes).hexdigest()
            registrar_licenca(
                db_path=db_path,
                email=email,
                hardware_id=None,
                emitida_em=datetime.datetime.utcnow().isoformat() + "Z",
                expira_em=None,
                tipo="perpetua",
                sha256_lic=sha256_hash,
                status="ativa",
                transaction_id=transaction_id
            )
            
            # Enviar e-mail
            enviar_email_licenca(email, lic_bytes, transaction_id)
            
            webhook_logger.info(f"Licença gerada e enviada com sucesso para {email} (Transação: {transaction_id})")
            return {"status": "success", "transaction_id": transaction_id, "email": email}
            
        except Exception as e:
            webhook_logger.error(f"Erro ao processar emissão automática para {email} (Transação {transaction_id}): {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro interno de processamento: {str(e)}")
            
    elif event in ["PURCHASE_CANCELED", "PURCHASE_REFUNDED"]:
        # Revogar licença no banco de dados local
        sucesso = revogar_licenca(db_path, transaction_id)
        if sucesso:
            webhook_logger.info(f"Licença vinculada à transação {transaction_id} marcada como REVOGADA devido ao evento {event}.")
            return {"status": "revoked", "transaction_id": transaction_id}
        else:
            webhook_logger.info(f"Evento de revogação {event} recebido para transação {transaction_id}, mas nenhuma licença correspondente foi encontrada.")
            return {"status": "ignored", "reason": "transaction_not_found", "transaction_id": transaction_id}
            
    else:
        webhook_logger.info(f"Evento {event} recebido para transação {transaction_id} e ignorado.")
        return {"status": "ignored", "reason": f"unhandled_event_{event}", "transaction_id": transaction_id}
