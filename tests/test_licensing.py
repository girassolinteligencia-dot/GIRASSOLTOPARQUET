import json
import base64
import datetime
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from app.core.licensing.validator import validar_licenca

class TestLicensing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Gerar par de chaves temporário para os testes
        cls.private_key = ec.generate_private_key(ec.SECP256R1())
        cls.public_key = cls.private_key.public_key()
        
    def _create_license_content(self, payload: dict) -> str:
        # Canonicalizar payload
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        # Assinar
        signature = self.private_key.sign(canonical_payload, ec.ECDSA(hashes.SHA256()))
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        # Retornar licença estruturada
        return json.dumps({
            "payload": payload,
            "signature": signature_b64
        })

    def _test_validation(self, license_str: str) -> dict:
        # Patch load_pem_public_key para retornar a chave pública de teste
        with patch("app.core.licensing.validator.load_pem_public_key", return_value=self.public_key):
            # Patch o os.path.exists para a chave pública sempre retornar True
            with patch("os.path.exists", return_value=True):
                return validar_licenca(license_str)

    def test_licenca_valida_perpetua(self):
        payload = {
            "email": "test@client.com",
            "hardware_id": None,
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": None,
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        res = self._test_validation(lic)
        
        self.assertTrue(res["valido"])
        self.assertEqual(res["payload"]["email"], "test@client.com")

    def test_licenca_valida_assinatura_futura(self):
        amanha = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        payload = {
            "email": "test@client.com",
            "hardware_id": None,
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": f"{amanha}T23:59:59Z",
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        res = self._test_validation(lic)
        
        self.assertTrue(res["valido"])

    def test_licenca_expirada(self):
        ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        payload = {
            "email": "test@client.com",
            "hardware_id": None,
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": f"{ontem}T23:59:59Z",
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        res = self._test_validation(lic)
        
        self.assertFalse(res["valido"])
        self.assertIn("expirou", res["mensagem"])

    def test_licenca_adulterada(self):
        payload = {
            "email": "test@client.com",
            "hardware_id": None,
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": None,
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        
        # Adulterar e-mail no payload manualmente
        data = json.loads(lic)
        data["payload"]["email"] = "hacker@client.com"
        adulterated_lic = json.dumps(data)
        
        res = self._test_validation(adulterated_lic)
        
        self.assertFalse(res["valido"])
        self.assertIn("adulterada", res["mensagem"])

    def test_licenca_hardware_id_vazio(self):
        payload = {
            "email": "test@client.com",
            "hardware_id": None,  # Vazio significa que não está travada
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": None,
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        
        # Mesmo com hardware_id divergente (mockado), deve passar porque a licença não é travada
        with patch("app.core.licensing.validator.obter_hardware_id", return_value="LOCAL-HW-ID"):
            res = self._test_validation(lic)
            
        self.assertTrue(res["valido"])

    def test_licenca_hardware_id_valido(self):
        payload = {
            "email": "test@client.com",
            "hardware_id": "LOCAL-HW-ID",
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": None,
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        
        # Com hardware ID local batendo com o da licença, deve passar
        with patch("app.core.licensing.validator.obter_hardware_id", return_value="LOCAL-HW-ID"):
            res = self._test_validation(lic)
            
        self.assertTrue(res["valido"])

    def test_licenca_hardware_id_divergente(self):
        payload = {
            "email": "test@client.com",
            "hardware_id": "CLIENT-HW-ID",
            "emitida_em": "2026-07-09T12:00:00Z",
            "expira_em": None,
            "produto": "GIRASSOLtoPARQUET",
            "versao_schema": 1
        }
        lic = self._create_license_content(payload)
        
        # Com hardware ID local divergente ("LOCAL-HW-ID" vs "CLIENT-HW-ID"), deve falhar
        with patch("app.core.licensing.validator.obter_hardware_id", return_value="LOCAL-HW-ID"):
            res = self._test_validation(lic)
            
        self.assertFalse(res["valido"])
        self.assertIn("vinculada a outro computador", res["mensagem"])
