import os
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess

# Adiciona o diretório raiz do projeto ao path para importar o validador Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.licensing.validator import validar_licenca

def read_private_key():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    priv_key_path = os.path.join(base_dir, "keys", "private_key.pem")
    if not os.path.exists(priv_key_path):
        priv_key_path = os.path.join("keys", "private_key.pem")
    with open(priv_key_path, "r", encoding="utf-8") as f:
        return f.read()

def write_dev_vars(private_key_content):
    dev_vars_path = os.path.join(os.path.dirname(__file__), ".dev.vars")
    with open(dev_vars_path, "w", encoding="utf-8") as f:
        f.write("HOTMART_HOTTOK=TEST_HOTTOK_123\n")
        f.write("RESEND_API_KEY=mock\n")
        f.write("EMAIL_REMETENTE=licencas@host.com\n")
        # Escapar quebras de linha para compatibilidade do wrangler com .dev.vars
        escaped_key = private_key_content.replace("\n", "\\n")
        f.write(f'LICENSE_PRIVATE_KEY="{escaped_key}"\n')

def main():
    print("=== INICIANDO TESTE DE COMPATIBILIDADE CRUZADA (TS -> PYTHON) ===")
    
    # 1. Carregar chave privada e escrever .dev.vars temporário
    try:
        priv_key = read_private_key()
        write_dev_vars(priv_key)
        print("-> .dev.vars configurado com sucesso.")
    except Exception as e:
        print(f"Erro ao ler chave ou escrever .dev.vars: {e}")
        sys.exit(1)
        
    # 2. Iniciar wrangler dev localmente
    print("-> Iniciando 'wrangler dev' local em segundo plano...")
    cmd = "npx wrangler dev --port 8787"
    wrangler_proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Aguardar o servidor subir
    print("-> Aguardando 6 segundos para o servidor local carregar...")
    time.sleep(6)
    
    # 3. Enviar requisição POST para o webhook
    url = "http://localhost:8787/webhook/hotmart"
    headers = {
        "X-Hotmart-Hottok": "TEST_HOTTOK_123",
        "Content-Type": "application/json"
    }
    payload = {
        "event": "PURCHASE_APPROVED",
        "data": {
            "buyer": {
                "email": "cliente_cross_test@provedor.com"
            },
            "purchase": {
                "transaction": "HP_CROSS_TEST_1001"
            }
        }
    }
    
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    
    success = False
    response_body = None
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                response_body = response.read().decode("utf-8")
                success = True
                print("-> Resposta HTTP 200 recebida com sucesso do Worker!")
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP do Worker: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Erro de conexão com o Worker: {e}")
        
    # 4. Encerrar o processo do wrangler dev de forma limpa
    print("-> Encerrando 'wrangler dev'...")
    try:
        if sys.platform == "win32":
            subprocess.run(f"taskkill /F /T /PID {wrangler_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            wrangler_proc.terminate()
            wrangler_proc.wait(timeout=2)
    except Exception:
        pass
        
    # 5. Limpar arquivo .dev.vars temporário
    try:
        dev_vars_path = os.path.join(os.path.dirname(__file__), ".dev.vars")
        if os.path.exists(dev_vars_path):
            os.remove(dev_vars_path)
            print("-> Arquivo temporário .dev.vars limpo.")
    except Exception:
        pass

    if not success or not response_body:
        print("ERRO: Não foi possível obter resposta válida do Worker local.")
        sys.exit(1)
        
    # 6. Analisar a licença retornada e validar via validador Python
    try:
        res_json = json.loads(response_body)
        license_str = res_json.get("license")
        if not license_str:
            print("ERRO: Resposta do Worker não contém a licença gerada.")
            sys.exit(1)
            
        print("-> Licença gerada recebida do Worker. Iniciando validação no cliente Python...")
        
        # Executar a validação usando a biblioteca python do cliente
        val_res = validar_licenca(license_str)
        
        if val_res.get("valido"):
            print("\n==================================================================")
            print(" SUCESSO! A assinatura gerada pelo Worker em TS foi validada")
            print(" com sucesso pelo validador Python do cliente!")
            print(f" E-mail da licença: {val_res['payload']['email']}")
            print(f" Hardware ID: {val_res['payload']['hardware_id']}")
            print("==================================================================\n")
            sys.exit(0)
        else:
            print(f"ERRO DE VALIDAÇÃO: {val_res.get('mensagem')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Erro ao processar validação da licença: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
