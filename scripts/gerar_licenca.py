import os
import sys
import argparse
import hashlib
import datetime
import json

# Add project root to path to ensure correct imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.licensing_core import (
    obter_caminho_db, registrar_licenca, gerar_licenca
)

def main():
    parser = argparse.ArgumentParser(description="Gerador de Licenças para o GIRASSOLtoPARQUET")
    parser.add_argument("--email", required=True, help="E-mail do cliente")
    parser.add_argument("--hardware-id", default="", help="Hardware ID da máquina do cliente (opcional)")
    parser.add_argument("--validade", default="", help="Data de validade (formato YYYY-MM-DD, opcional para perpétua)")
    parser.add_argument("--tipo", choices=["perpetua", "assinatura"], default="perpetua", help="Tipo de licença")
    
    args = parser.parse_args()
    
    # 1. Obter caminho do DB
    db_path = obter_caminho_db()
    
    try:
        # 2. Gerar conteúdo da licença usando o módulo core
        licenca_bytes = gerar_licenca(
            email=args.email,
            hardware_id=args.hardware_id or None,
            validade=args.validade or None,
            tipo=args.tipo
        )
        
        # 3. Salvar o arquivo local license.lic
        output_path = "license.lic"
        with open(output_path, "wb") as f:
            f.write(licenca_bytes)
            
        # 4. Extrair metadados para registrar no DB
        licenca_data = json.loads(licenca_bytes.decode('utf-8'))
        payload = licenca_data["payload"]
        emitida_em = payload["emitida_em"]
        expira_em = payload["expira_em"]
        
        # 5. Calcular o hash do arquivo gerado
        sha256_hash = hashlib.sha256(licenca_bytes).hexdigest()
        
        # 6. Registrar no DB
        registrar_licenca(
            db_path=db_path,
            email=args.email,
            hardware_id=args.hardware_id or None,
            emitida_em=emitida_em,
            expira_em=expira_em,
            tipo=args.tipo,
            sha256_lic=sha256_hash,
            status="ativa",
            transaction_id=None
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
        
    except Exception as e:
        print(f"Erro ao gerar licença: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
