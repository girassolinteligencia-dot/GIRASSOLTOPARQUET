import os
import sys
import json
import base64
import datetime
import hashlib
import sqlite3
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def obter_caminho_db() -> str:
    """Retorna o caminho padrão do banco de dados SQLite."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, "scripts")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "registro_licencas.db")

def init_db(db_path: str):
    """Inicializa o banco de dados e executa migrações automáticas se necessário."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_licencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            hardware_id TEXT,
            emitida_em TEXT NOT NULL,
            expira_em TEXT,
            tipo TEXT NOT NULL,
            sha256_licenca TEXT NOT NULL
        )
    """)
    conn.commit()
    
    # Migrações automáticas para adicionar novas colunas
    cursor.execute("PRAGMA table_info(registro_licencas)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "status" not in columns:
        print("Migração: Adicionando coluna 'status' ao banco de dados.")
        cursor.execute("ALTER TABLE registro_licencas ADD COLUMN status TEXT DEFAULT 'ativa'")
        conn.commit()
        
    if "transaction_id" not in columns:
        print("Migração: Adicionando coluna 'transaction_id' ao banco de dados.")
        cursor.execute("ALTER TABLE registro_licencas ADD COLUMN transaction_id TEXT")
        conn.commit()
        
    conn.close()

def registrar_licenca(db_path: str, email: str, hardware_id: str | None, emitida_em: str, 
                      expira_em: str | None, tipo: str, sha256_lic: str, 
                      status: str = "ativa", transaction_id: str | None = None):
    """Registra uma nova licença no banco de dados SQLite."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registro_licencas (email, hardware_id, emitida_em, expira_em, tipo, sha256_licenca, status, transaction_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (email, hardware_id, emitida_em, expira_em, tipo, sha256_lic, status, transaction_id))
    conn.commit()
    conn.close()

def revogar_licenca(db_path: str, transaction_id: str) -> bool:
    """Marca o status de uma licença específica como 'revogada' com base no transaction_id."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se a licença existe
    cursor.execute("SELECT id FROM registro_licencas WHERE transaction_id = ?", (transaction_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
        
    cursor.execute("""
        UPDATE registro_licencas 
        SET status = 'revogada' 
        WHERE transaction_id = ?
    """, (transaction_id,))
    conn.commit()
    conn.close()
    return True

def buscar_licenca_por_transaction_id(db_path: str, transaction_id: str) -> dict | None:
    """Busca uma licença registrada pelo ID da transação da Hotmart."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registro_licencas WHERE transaction_id = ?", (transaction_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def gerar_licenca(email: str, hardware_id: str | None, validade: str | None, tipo: str) -> bytes:
    """
    Gera o conteúdo de uma licença signed ECDSA.
    Retorna o JSON da licença serializado em bytes.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    priv_key_path = os.path.join(base_dir, "keys", "private_key.pem")
    
    if not os.path.exists(priv_key_path):
        # Fallback para execução local a partir da raiz do projeto
        priv_key_path = os.path.join("keys", "private_key.pem")
        
    if not os.path.exists(priv_key_path):
        raise FileNotFoundError(f"Chave privada mestre não encontrada no caminho '{priv_key_path}'.")
        
    # 1. Carrega a chave privada
    with open(priv_key_path, "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)
        
    # 2. Prepara as datas
    emitida_em = datetime.datetime.utcnow().isoformat() + "Z"
    expira_em = None
    
    if tipo == "assinatura":
        if not validade:
            raise ValueError("Licenças do tipo 'assinatura' exigem uma data de validade (YYYY-MM-DD).")
        validade_date = datetime.date.fromisoformat(validade)
        expira_em = validade_date.isoformat() + "T23:59:59Z"
    elif validade:
        validade_date = datetime.date.fromisoformat(validade)
        expira_em = validade_date.isoformat() + "T23:59:59Z"
        
    payload = {
        "email": email,
        "hardware_id": hardware_id.upper() if hardware_id else None,
        "emitida_em": emitida_em,
        "expira_em": expira_em,
        "produto": "GIRASSOLtoPARQUET",
        "versao_schema": 1
    }
    
    # 3. Canonicaliza o payload JSON (compacto, ordenado)
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    # 4. Assina o payload com a chave privada
    signature = private_key.sign(canonical_payload, ec.ECDSA(hashes.SHA256()))
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # 5. Constrói o objeto de licença
    licenca_completa = {
        "payload": payload,
        "signature": signature_b64
    }
    
    return json.dumps(licenca_completa, indent=2, ensure_ascii=False).encode('utf-8')
