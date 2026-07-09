import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def main():
    # 1. Criar pastas necessárias
    os.makedirs("keys", exist_ok=True)
    os.makedirs("app/core/licensing", exist_ok=True)
    
    # 2. Gerar chaves ECDSA P-256
    print("Gerando par de chaves ECDSA (NIST P-256)...")
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # 3. Serializar chave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 4. Serializar chave pública
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # 5. Salvar nos arquivos
    private_path = os.path.join("keys", "private_key.pem")
    public_path = os.path.join("app", "core", "licensing", "public_key.pem")
    
    with open(private_path, "wb") as f:
        f.write(private_pem)
        
    with open(public_path, "wb") as f:
        f.write(public_pem)
        
    print(f"Sucesso! Chave pública salva em: {public_path}")
    print(f"Sucesso! Chave privada salva em: {private_path} (mantenha-a segura e ignore-a no git).")

if __name__ == "__main__":
    main()
