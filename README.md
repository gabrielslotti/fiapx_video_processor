# Video Processing Service  
  
Este é um serviço de processamento de vídeos que permite fazer upload de vídeos e extrair frames em formato ZIP. O serviço é construído usando FastAPI, Celery, e PostgreSQL, oferecendo processamento assíncrono e escalável.  
  
## Funcionalidades  
  
- Upload de vídeos  
- Processamento assíncrono de vídeos  
- Extração de frames em intervalos configuráveis  
- Download dos frames em arquivo ZIP  
- Autenticação de usuários  
- Rastreamento de status de processamento  
- API RESTful protegida  

## Arquitetura do Projeto de Processamento de Vídeo
![image](https://github.com/user-attachments/assets/b4bfe42f-dab4-43f1-970c-f83972c1c5b0)


### Descrição dos Componentes:
1. User (Cliente/Frontend):
- Interface para usuários fazerem upload de vídeos
- Visualização do status de processamento
- Download dos arquivos processados

2. API FastAPI:
- Gerencia autenticação de usuários
- Recebe uploads de vídeos
- Envia tarefas para processamento
- Fornece endpoints para status e download

3. PostgreSQL:
- Armazena dados de usuários
- Mantém registro de vídeos
- Rastreia estado de processamento

4. Redis:
- Atua como message broker para Celery
- Gerencia fila de tarefas
- Armazena resultados temporários

5. Celery Worker:
- Processa vídeos de forma assíncrona
- Atualiza status no banco de dados
- Gerencia arquivos de vídeo e extrações

6. OpenCV (Video Processing):
- Extrai frames de vídeos
- Compacta resultados em ZIP

7. Email Service:
- Envia email para o usuário

8. GCS (Google Cloud Storage):
- Armazena vídeos e resultados processados

### Fluxo da Arquitetura

1. Usuário no Frontend faz POST /videos/upload na API.
2. A API salva o vídeo no bucket GCS e grava um registro no PostgreSQL com status PENDING.
3. A API enfileira uma tarefa no Redis (Celery broker) com o nome do objeto de entrada e o ID do vídeo.
4. O Celery Worker, rodando em outro serviço Cloud Run, consome a tarefa:
- Faz download do vídeo do GCS para /tmp.
- Processa frames via OpenCV e empacota em um ZIP.
- Sobe o ZIP de volta para o GCS.
- Atualiza o status do vídeo no PostgreSQL para COMPLETED e armazena o nome do objeto de saída.
5. O Worker gera um Signed URL (tempo‐limitado) para o ZIP e envia um email ao usuário via SMTP (Gmail).
6. O usuário clica no link do email e faz download direto do GCS, sem precisar autenticar na API.

### Essa arquitetura garante:
- Desacoplamento entre API e processamento (Celery).
- Persistência e rastreamento de estado no PostgreSQL.
- Fila de tarefas confiável com Redis.
- Armazenamento escalável de arquivos em GCS.
- Download seguro via Signed URLs.
- Notificação via SMTP sem expor credenciais em links.
- Escalabilidade horizontal (mais workers podem ser adicionados)
- Processamento assíncrono (não bloqueia a API)
- Tolerância a falhas (tarefas são persistidas)
- Balanceamento de carga entre workers

## Requisitos  
  
- Python 3.9+  
- PostgreSQL  
- Redis
- Celery
- UV (gerenciador de pacotes Python)
- Flower (opcional)  
- Docker e Docker Compose (opcional)  
  
## Configuração Local  
  
1. Clone o repositório:  
```bash
git clone https://github.com/seu-usuario/video-processing-service.git  
cd video-processing-service
```

2. Crie um ambiente virtual e instale as dependências:
```bash
uv venv  # Cria ambiente virtual

source venv/bin/activate  # Linux/Mac  
# OU
.\venv\Scripts\activate  # Windows  
  
uv sync  # Sincroniza as dependências (opcional)
```

3.  Configure as variáveis de ambiente (.env):
```bash
# Database
DB_USER=postgres
DB_PORT=5432
DB_PASSWORD=postgres
DB_NAME=video_service
DB_HOST=localhost

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=sua-secret-key

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 1440 = 1 dia
```

4.  Inicie os serviços com Docker Compose (opcional):
```bash
docker-compose up -d
```

5.  Execute as migrações do banco de dados:
```bash
alembic upgrade head
```
6.  Inicie a API:
```bash
uv run uvicorn main:app --reload
```

7.  Em outro terminal, inicie o worker do Celery:
```bash
celery -A app.workers.celery_worker worker --loglevel=info
```

## Uso da API

### Criar usuário
```bash
curl -X POST http://localhost:8000/users/ \  
-H "Content-Type: application/json" \  
-d '{"email": "user@example.com", "password": "password123"}'
```
  
### Obter token
```bash
curl -X POST http://localhost:8000/auth/token \  
-d "username=user@example.com&password=password123" \  
-H "Content-Type: application/x-www-form-urlencoded"
```

### Upload de Vídeo
```bash
curl -X POST http://localhost:8000/videos/upload \  
-H "Authorization: Bearer {seu-token}" \  
-F "file=@seu-video.mp4"
```
### Verificar Status
```bash
curl http://localhost:8000/videos/status \  
-H "Authorization: Bearer {seu-token}"
```

### Download do Resultado (arquivo zipado)
```bash
curl http://localhost:8000/videos/download/{video_id} \  
-H "Authorization: Bearer {seu-token}" \  
--output frames.zip
```

## Monitoramento

O Flower está disponível para monitoramento das tarefas do Celery:

http://localhost:5555

## Testes

Execute os testes com:
```bash
pytest
```
## Docker

Para executar todo o ambiente com Docker:
```bash
docker-compose up --build
```
Isso iniciará:

- API FastAPI
- Worker Celery
- PostgreSQL
- Redis
- Flower (monitoramento)

## CI/CD

O projeto inclui GitHub Actions para:

- Execução de testes
- Verificação de código
- Build e push de imagens Docker
- Deploy automático (configurável)

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo  LICENSE  para detalhes. 
