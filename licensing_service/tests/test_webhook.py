import os
import tempfile
import sqlite3
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Configurar variáveis de ambiente antes de importar o main
os.environ["HOTMART_HOTTOK"] = "TEST_TOKEN_123"
os.environ["SMTP_HOST"] = "smtp.host.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USER"] = "test@host.com"
os.environ["SMTP_PASSWORD"] = "pass"
os.environ["EMAIL_REMETENTE"] = "licencas@host.com"

from licensing_service.main import app
from scripts.licensing_core import init_db

class TestWebhookService(unittest.TestCase):
    def setUp(self):
        # 1. Configurar banco de dados SQLite temporário para os testes
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        init_db(self.temp_db_path)
        
        # 2. Patch do caminho do banco para usar o temporário em main.py
        self.db_patcher = patch("licensing_service.main.obter_caminho_db", return_value=self.temp_db_path)
        self.mock_db_path = self.db_patcher.start()
        
        # 3. Inicializar TestClient do FastAPI
        self.client = TestClient(app)

    def tearDown(self):
        # Desativar patcher
        self.db_patcher.stop()
        
        # Fechar e apagar o banco temporário
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_webhook_unauthorized(self):
        # Envia requisição sem token
        response = self.client.post("/webhook/hotmart", json={"event": "PURCHASE_APPROVED"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("token", response.json()["detail"].lower())

        # Envia requisição com token errado
        response = self.client.post(
            "/webhook/hotmart", 
            headers={"X-HOTMART-HOTTOK": "WRONG_TOKEN"},
            json={"event": "PURCHASE_APPROVED"}
        )
        self.assertEqual(response.status_code, 401)

    @patch("licensing_service.main.enviar_email_licenca")
    def test_webhook_purchase_approved_success(self, mock_send_email):
        payload = {
            "event": "PURCHASE_APPROVED",
            "data": {
                "buyer": {
                    "email": "cliente@provedor.com"
                },
                "purchase": {
                    "transaction": "HP_APPROVED_123"
                }
            }
        }
        
        response = self.client.post(
            "/webhook/hotmart",
            headers={"X-HOTMART-HOTTOK": "TEST_TOKEN_123"},
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["transaction_id"], "HP_APPROVED_123")
        
        # Verificar se o e-mail foi "enviado"
        mock_send_email.assert_called_once()
        
        # Verificar se foi registrado no banco
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT email, status, transaction_id FROM registro_licencas WHERE transaction_id = ?", ("HP_APPROVED_123",))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "cliente@provedor.com")
        self.assertEqual(row[1], "ativa")
        self.assertEqual(row[2], "HP_APPROVED_123")

    @patch("licensing_service.main.enviar_email_licenca")
    def test_webhook_idempotency(self, mock_send_email):
        payload = {
            "event": "PURCHASE_APPROVED",
            "data": {
                "buyer": {
                    "email": "cliente@provedor.com"
                },
                "purchase": {
                    "transaction": "HP_IDEMPOTENCY_999"
                }
            }
        }
        
        # Primeira requisição (sucesso)
        response1 = self.client.post(
            "/webhook/hotmart",
            headers={"X-HOTMART-HOTTOK": "TEST_TOKEN_123"},
            json=payload
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()["status"], "success")
        
        # Segunda requisição (deve ignorar e retornar 200 silencioso)
        response2 = self.client.post(
            "/webhook/hotmart",
            headers={"X-HOTMART-HOTTOK": "TEST_TOKEN_123"},
            json=payload
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()["status"], "ignored")
        self.assertEqual(response2.json()["reason"], "already_processed")
        
        # E-mail deve ter sido enviado apenas 1 vez no total
        self.assertEqual(mock_send_email.call_count, 1)

    @patch("licensing_service.main.enviar_email_licenca")
    def test_webhook_refund_and_cancel(self, mock_send_email):
        # 1. Primeiro criar uma licença ativa
        payload_approve = {
            "event": "PURCHASE_APPROVED",
            "data": {
                "buyer": {
                    "email": "refunded@provedor.com"
                },
                "purchase": {
                    "transaction": "HP_TRANS_REFUND"
                }
            }
        }
        self.client.post(
            "/webhook/hotmart",
            headers={"X-HOTMART-HOTTOK": "TEST_TOKEN_123"},
            json=payload_approve
        )
        
        # Confirmar estado inicial ativo
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM registro_licencas WHERE transaction_id = ?", ("HP_TRANS_REFUND",))
        self.assertEqual(cursor.fetchone()[0], "ativa")
        conn.close()
        
        # 2. Enviar evento de reembolso
        payload_refund = {
            "event": "PURCHASE_REFUNDED",
            "data": {
                "purchase": {
                    "transaction": "HP_TRANS_REFUND"
                }
            }
        }
        
        response = self.client.post(
            "/webhook/hotmart",
            headers={"X-HOTMART-HOTTOK": "TEST_TOKEN_123"},
            json=payload_refund
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "revoked")
        
        # Confirmar que foi marcada como revogada no banco
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM registro_licencas WHERE transaction_id = ?", ("HP_TRANS_REFUND",))
        self.assertEqual(cursor.fetchone()[0], "revogada")
        conn.close()
