import os
import sys
import json
import base64
import datetime
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from app.core.licensing.hardware_id import obter_hardware_id

def obter_caminho_licenca() -> str:
    local_app_data = os.path.expandvars(r"%LOCALAPPDATA%")
    if local_app_data == "%LOCALAPPDATA%":
        local_app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    config_dir = os.path.join(local_app_data, "ConversorParquetOffline")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "license.lic")

def validar_licenca(conteudo_licenca: str) -> dict:
    try:
        data = json.loads(conteudo_licenca)
        payload = data.get("payload")
        signature_b64 = data.get("signature")
        if not payload or not signature_b64:
            return {"valido": False, "mensagem": "Arquivo de licença corrompido ou formato inválido."}
        
        # 1. Carregar a chave pública
        pub_key_path = os.path.join(os.path.dirname(__file__), "public_key.pem")
        if not os.path.exists(pub_key_path):
            return {"valido": False, "mensagem": f"Erro interno: Chave pública não encontrada em {pub_key_path}."}
            
        with open(pub_key_path, "rb") as f:
            public_key = load_pem_public_key(f.read())
            
        # 2. Canonicalizar o payload
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
        # 3. Decodificar a assinatura
        signature = base64.b64decode(signature_b64)
        
        # 4. Verificar a assinatura ECDSA
        try:
            public_key.verify(signature, canonical_payload, ec.ECDSA(hashes.SHA256()))
        except Exception:
            return {"valido": False, "mensagem": "Assinatura digital da licença é inválida (licença adulterada)."}
            
        # 5. Validar data de expiração
        expira_em = payload.get("expira_em")
        if expira_em:
            try:
                # Tratar formato ISO 8601, e.g. "YYYY-MM-DD"
                if len(expira_em) >= 10:
                    exp_date = datetime.datetime.fromisoformat(expira_em[:10]).date()
                else:
                    return {"valido": False, "mensagem": "Formato de data de expiração inválido na licença."}
                
                hoje = datetime.date.today()
                if hoje > exp_date:
                    return {"valido": False, "mensagem": f"Licença expirou em {expira_em}. Entre em contato com o suporte."}
            except Exception:
                return {"valido": False, "mensagem": "Erro ao processar data de expiração da licença."}
                
        # 6. Validar hardware ID se estiver preenchido
        hw_id_licenca = payload.get("hardware_id")
        if hw_id_licenca:  # Se estiver preenchido (vazio/None = não travado)
            hw_id_local = obter_hardware_id()
            if hw_id_licenca.upper() != hw_id_local.upper():
                return {
                    "valido": False,
                    "mensagem": "Esta licença está vinculada a outro computador. Entre em contato para reemissão."
                }
                
        return {"valido": True, "mensagem": "Licença válida.", "payload": payload}
        
    except Exception as e:
        return {"valido": False, "mensagem": f"Falha na validação da licença: {str(e)}"}

def obter_status_licenca() -> dict:
    caminho = obter_caminho_licenca()
    if not os.path.exists(caminho):
        return {"valido": False, "mensagem": "Licença não encontrada. Ativação necessária."}
        
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        return validar_licenca(conteudo)
    except Exception as e:
        return {"valido": False, "mensagem": f"Não foi possível ler o arquivo de licença: {str(e)}"}
