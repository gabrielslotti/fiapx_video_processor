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

┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │
│  Cliente/       │       │  API FastAPI    │       
│  Frontend       │◄─────►│  (Container)    │       
│                 │       │                 │       
└─────────────────┘       └────────┬────────┘       
                                   │                
                                   ▼                
┌─────────────────┐       ┌────────┴────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  PostgreSQL     │◄─────►│  Redis          │◄─────►│  Celery Worker  │
│  (Container)    │       │  (Container)    │       │  (Container)    │
│                 │       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │                 │
                                                    │  OpenCV         │
                                                    │  Video          │
                                                    │  Processing     │
                                                    │                 │
                                                    └─────────────────┘


### Descrição dos Componentes:
1. Cliente/Frontend:
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

### Fluxo de Dados
1. Usuário faz login e upload de vídeo
2. API valida arquivo e cria registro no banco
3. API submete tarefa para Redis
4. Celery Worker consome tarefa da fila
5. Worker processa vídeo extraindo frames
6. Frames são compactados em arquivo ZIP
7. Status é atualizado no banco de dados
8. Usuário recebe notificação de conclusão
9. Usuário pode baixar arquivo ZIP com frames

### Esta arquitetura distribuída permite:
- Escalabilidade horizontal (mais workers podem ser adicionados)
- Processamento assíncrono (não bloqueia a API)
- Tolerância a falhas (tarefas são persistidas)
- Balanceamento de carga entre workers

## Requisitos  
  
- Python 3.9+  
- PostgreSQL  
- Redis
- RabbitMQ
-  Celery
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

-   API FastAPI
-   Worker Celery
-   PostgreSQL
-   Redis
-  RabbitMQ
-   Flower (monitoramento)

## CI/CD

O projeto inclui GitHub Actions para:

-   Execução de testes
-   Verificação de código
-   Build e push de imagens Docker
-   Deploy automático (configurável)

## Contribuindo

1.  Fork o projeto
2.  Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3.  Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4.  Push para a branch (`git push origin feature/nova-feature`)
5.  Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo  LICENSE  para detalhes. 