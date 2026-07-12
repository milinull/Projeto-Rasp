import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


class ClienteTimescaleDB:
    """
    Classe responsável por conectar ao TimescaleDB e registrar
    os logs de áudio da UTI de forma estruturada.
    """

    def __init__(self, id_microfone=21):
        # Captura as variáveis de ambiente (garanta que estão carregadas no Python)
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB", "uti_audio_db")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "senha_super_segura_uti")

        # Dados de contexto da Placa
        self.setor = "UTI-A"
        self.leito = "Leito 07"
        self.id_microfone = id_microfone

    def conectar(self):
        """Estabelece a conexão com o banco de dados"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
            )
            return conn
        except Exception as e:
            print(f"[ERRO] Falha ao conectar no TimescaleDB: {e}")
            return None

    def registrar_evento(self, estado_aviso: str, volume_pico: float, duracao: float):
        """
        Salva um alerta imediato (AMARELO ou VERMELHO) no banco de dados.
        """
        conn = self.conectar()
        if not conn:
            return

        # Pega a hora exata e zera os milissegundos
        horario_atual = datetime.now(timezone.utc).replace(microsecond=0)

        # Força a conversão de tipos NumPy para tipos nativos do Python
        # Arredonda o volume e a duração para 2 casas decimais
        volume_pico_nativo = round(float(volume_pico), 2)
        duracao_nativa = round(float(duracao), 2)

        query = """
            INSERT INTO sensor_data.monitoramento_audio 
            (horario, id_microfone, setor, leito, estado_aviso, volume_registrado, duracao_segundos, tipo_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        valores = (
            horario_atual,
            self.id_microfone,
            self.setor,
            self.leito,
            estado_aviso,
            volume_pico_nativo,
            duracao_nativa,
            "EVENTO",
        )

        try:
            cursor = conn.cursor()
            cursor.execute(query, valores)  # [cite: 95]
            conn.commit()
            cursor.close()
            print(
                f"[DB LOG] Evento de alerta ({estado_aviso}) gravado com sucesso."
            )  # [cite: 87]
        except Exception as e:
            print(f"[ERRO] Falha ao salvar evento: {e}")  # [cite: 87]
        finally:
            conn.close()  # [cite: 87]

    def registrar_baseline(self, volume_medio: float):
        """
        Salva a média de ruído do ambiente a cada 1 ou 5 minutos (VERDE)[cite: 88].
        Serve como 'Prova de Vida' e base para relatórios[cite: 88].
        """
        conn = self.conectar()
        if not conn:
            return

        # Pega a hora exata e zera os milissegundos
        horario_atual = datetime.now(timezone.utc).replace(microsecond=0)

        # Força a conversão de tipos NumPy para tipos nativos do Python
        # Arredonda a média para 2 casas decimais
        volume_medio_nativo = round(float(volume_medio), 2)

        query = """
            INSERT INTO sensor_data.monitoramento_audio 
            (horario, id_microfone, setor, leito, estado_aviso, volume_registrado, duracao_segundos, tipo_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        # Duração nula ou fixa, já que é uma média
        valores = (
            horario_atual,
            self.id_microfone,
            self.setor,
            self.leito,
            "VERDE",
            volume_medio_nativo,
            0.0,
            "BASELINE",
        )

        try:
            cursor = conn.cursor()
            cursor.execute(query, valores)  # [cite: 90, 95]
            conn.commit()  # [cite: 90]
            cursor.close()  # [cite: 90]
            print(
                "[DB LOG] Baseline do ambiente (Verde) gravado com sucesso."
            )  # [cite: 90]
        except Exception as e:
            print(f"[ERRO] Falha ao salvar baseline: {e}")  # [cite: 90]
        finally:
            conn.close()  # [cite: 90]
