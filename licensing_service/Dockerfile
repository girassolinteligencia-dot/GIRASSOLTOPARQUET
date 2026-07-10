FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY licensing_service/requirements.txt /app/licensing_service/requirements.txt
RUN pip install --no-cache-dir -r licensing_service/requirements.txt

# Copiar arquivos necessários do serviço e diretórios compartilhados
COPY licensing_service /app/licensing_service
COPY scripts /app/scripts
COPY keys /app/keys

# Expor a porta padrão da aplicação
EXPOSE 8000

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Comando de inicialização
CMD ["uvicorn", "licensing_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
