# AcoustiCare (Monitoramento Acústico Hospitalar)

Este projeto implementa um sistema de telemetria e microfonação focado em Unidades de Terapia Intensiva (UTI). O objetivo é monitorar continuamente (24/7) o nível de ruído no ambiente, fornecendo feedback visual imediato para a equipe médica por meio de um painel clínico e registrando os dados em um banco de dados de séries temporais para futuras auditorias e gestão acústica.

## Arquitetura e Fluxo de Dados

O sistema utiliza uma abordagem híbrida inteligente para otimizar o processamento e o uso de rede:

- **Envio Baseado em Eventos (Alertas):** Quando o sistema detecta conversas ou vozes altas (mudando o estado para Amarelo ou Vermelho), um log com o pico de volume e a duração do evento é gravado instantaneamente no banco de dados através de processamento em _threads_, sem interromper a captação de áudio.
- **Envio Periódico (Baseline):** Durante os períodos de silêncio (Verde), o sistema calcula a média de volume e envia um pacote único a cada minuto. Isso define a métrica base de ruído do leito e funciona como "Prova de Vida" (Uptime) do dispositivo.

## Recursos e Usabilidade da Interface (Frontend)

O painel clínico (`clinical.html`) foi desenhado para ser responsivo, focado no uso em telas de 7 polegadas (tablets) e operado via _touchscreen_. Toda a comunicação com o backend ocorre em tempo real via WebSockets.

- **Feedback Visual Imediato:** O cartão central muda de cor (Verde, Amarelo, Vermelho) e de texto ("Silêncio", "Conversa", "Fala Alta") instantaneamente conforme o processamento acústico.
- **Menu de Configurações Dinâmico:** Um botão de engrenagem no cabeçalho abre um modal sobreposto com fundo desfocado, mantendo o foco do usuário nas configurações.
- **Mapeamento Automático de Microfones:** Ao abrir o menu, a interface solicita ao Python os dispositivos de entrada conectados ao sistema operacional e monta um menu suspenso sem necessidade de recarregar a página.
- **Controle de Ganho Digital:** Uma barra deslizante permite ajustar o ganho do microfone (de -15 a +15) em tempo real. A barra reseta automaticamente para zero ao trocar de dispositivo para evitar estouros de áudio.
- **VU Meter (Teste de Nível):** Uma barra indicadora preenche dinamicamente (de 0 a 100%) mostrando a captação exata de volume do microfone selecionado.

## Tecnologias e Bibliotecas Utilizadas

- **Linguagem:** Python 3.12
- **Bibliotecas Python:**
  - `numpy`: Para cálculos matemáticos e RMS do áudio.
  - `sounddevice`: Para captura de áudio assíncrona do sistema operacional.
  - `websockets`: Para comunicação bidirecional em tempo real com a interface.
  - `psycopg2`: Para integração e inserção de dados no banco PostgreSQL.
  - `python-dotenv`: Para carregamento seguro de variáveis de ambiente.
- **Infraestrutura:** Docker e Docker Compose.
- **Banco de Dados:** TimescaleDB (PostgreSQL otimizado para séries temporais).

## Estrutura do Projeto

- `/Scripts/`
  - `ciclos_audio.py`: Algoritmo que processa a matemática do áudio, picos e define os estados clínicos.
  - `db_client.py`: Gerencia a conexão e as inserções (eventos e baselines) no TimescaleDB.
  - `websocket_server.py`: Servidor que envia telemetria e recebe comandos do HTML.
- `/Sql/`
  - `monitoramento_audio.sql`: Script de criação do schema e da _Hypertable_ no banco de dados.
- `/Frontend/` (Opcional, caso CSS e JS estejam separados)
  - `clinical.html`: Interface visual do painel da UTI.
- `main.py`: Orquestrador principal. Inicia a captação de áudio, o WebSocket e o controle do banco de dados simultaneamente.
- `docker-compose.yaml` e `.env`: Arquivos de configuração da infraestrutura de banco de dados.

## Requisitos e Instalação

1. Certifique-se de ter o **Python 3.12** e o **Docker** instalados em seu ambiente.
2. Crie um ambiente virtual e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com as credenciais do banco de dados:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=sua_senha_segura
   POSTGRES_DB=uti_audio_db
   POSTGRES_PORT=5432
   POSTGRES_HOST=localhost
   PGADMIN_DEFAULT_EMAIL=admin@admin.com
   PGADMIN_DEFAULT_PASSWORD=senha_admin
   ```

## Subindo a Infraestrutura (Docker)

O projeto utiliza o Docker para hospedar o banco de dados sem poluir o sistema operacional local.

1. Inicie os contêineres em segundo plano:
   ```bash
   docker-compose up -d
   ```
2. Acesse o gerenciador do banco de dados (pgAdmin) pelo navegador em `http://localhost:8080` utilizando as credenciais definidas no `.env`.
3. Conecte-se ao servidor (Host: `iot_timescaledb`, Porta: `5432`) e execute o script SQL contido na pasta `/Sql/` para criar a tabela estruturada.

## Executando o Sistema

Para iniciar a captação de áudio e a integração com o banco de dados e a interface, execute na raiz do projeto:

```bash
python main.py
```

O terminal exibirá um log visual da captação. Para utilizar a interface, basta abrir o arquivo `clinical.html` em qualquer navegador moderno. Ajustes de ganho e trocas de microfone feitos pela interface serão aplicados imediatamente pelo script Python.
