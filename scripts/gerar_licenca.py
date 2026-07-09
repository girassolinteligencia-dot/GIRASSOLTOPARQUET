import os
import sys
import json
import base64
import datetime
import argparse
import hashlib
import sqlite3
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
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
    conn.close()

def registrar_licenca(db_path: str, email: str, hardware_id: str, emitida_em: str, expira_em: str, tipo: str, sha256_lic: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registro_licencas (email, hardware_id, emitida_em, expira_em, tipo, sha256_licenca)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (email, hardware_id, emitida_em, expira_em, tipo, sha256_lic))
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Gerador de Licenças para o GIRASSOLtoPARQUET")
    parser.add_argument("--email", required=True, help="E-mail do cliente")
    parser.add_argument("--hardware-id", default="", help="Hardware ID da máquina do cliente (opcional)")
    parser.add_argument("--validade", default="", help="Data de validade (formato YYYY-MM-DD, opcional para perpétua)")
    parser.add_argument("--tipo", choices=["perpetua", "assinatura"], default="perpetua", help="Tipo de licença")
    
    args = parser.parse_args()
    
    priv_key_path = os.path.join("keys", "private_key.pem")
    if not os.path.exists(priv_key_path):
        print(f"Erro: Chave privada não encontrada em '{priv_key_path}'. Execute 'gerar_chaves_mestre.py' primeiro.")
        sys.exit(1)
        
    # 1. Carrega a chave privada
    with open(priv_key_path, "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)
        
    # 2. Prepara o payload
    emitida_em = datetime.datetime.utcnow().isoformat() + "Z"
    expira_em = None
    if args.tipo == "assinatura":
        if not args.validade:
            print("Erro: Licenças do tipo 'assinatura' exigem uma data de --validade (YYYY-MM-DD).")
            sys.exit(1)
        try:
            # Validar formato
            validade_date = datetime.date.fromisoformat(args.validade)
            expira_em = validade_date.isoformat() + "T23:59:59Z"
        except ValueError:
            print("Erro: Data de validade deve estar no formato YYYY-MM-DD.")
            sys.exit(1)
    elif args.validade:
        try:
            validade_date = datetime.date.fromisoformat(args.validade)
            expira_em = validade_date.isoformat() + "T23:59:59Z"
        except ValueError:
            print("Erro: Data de validade deve estar no formato YYYY-MM-DD.")
            sys.exit(1)
            
    payload = {
        "email": args.email,
        "hardware_id": args.hardware_id.upper() if args.hardware_id else None,
        "emitida_em": emitida_em,
        "expira_em": expira_em,
        "produto": "GIRASSOLtoPARQUET",
        "versao_schema": 1
    }
    
    # 3. Canonicaliza o JSON (compacto, ordenado)
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    # 4. Assina o payload
    signature = private_key.sign(canonical_payload, ec.ECDSA(hashes.SHA256()))
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # 5. Constrói o objeto de licença
    licenca_completa = {
        "payload": payload,
        "signature": signature_b64
    }
    
    licenca_json = json.dumps(licenca_completa, indent=2, ensure_ascii=False)
    
    # 6. Salva o arquivo license.lic
    output_path = "license.lic"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(licenca_json)
        
    # 7. Registra no banco de dados local
    db_path = os.path.join("scripts", "registro_licencas.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_db(db_path)
    
    # Calcula hash SHA-256 do arquivo gerado
    sha256_hash = hashlib.sha256(licenca_json.encode('utf-8')).hexdigest()
    registrar_licenca(
        db_path=db_path,
        email=args.email,
        hardware_id=args.hardware_id or None,
        emitida_em=emitida_em,
        expira_em=expira_em,
        tipo=args.tipo,
        sha256_lic=sha256_hash
    )
    
    print(f"\nLicença gerada com sucesso e salva em '{output_path}'!")
    print(f"E-mail: {args.email}")
    print(f"Tipo: {args.tipo}")
    if args.hardware_id:
        print(f"Hardware Lock: {args.hardware_id.upper()}")
    if expira_em:
        print(f"Expira em: {expira_em}")
    print(f"Hash da Licença: {sha256_hash}")
    print(f"Registro gravado em: {db_path}")

if __name__ == "__main__":
    main()
