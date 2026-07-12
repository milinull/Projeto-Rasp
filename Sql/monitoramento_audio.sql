-- Cria o schema para organizar os dados de sensores da UTI
CREATE SCHEMA IF NOT EXISTS sensor_data;

-- Cria a tabela padrão referenciando o novo schema
CREATE TABLE sensor_data.monitoramento_audio (
    horario TIMESTAMPTZ NOT NULL,
    id_microfone INT NOT NULL,
    setor VARCHAR(50) NOT NULL,
    leito VARCHAR(50) NOT NULL,
    estado_aviso VARCHAR(20) NOT NULL,
    volume_registrado FLOAT NOT NULL,
    duracao_segundos FLOAT,
    tipo_registro VARCHAR(20) NOT NULL
);

-- Transforma a tabela em Hypertable baseada no tempo, referenciando o schema
SELECT create_hypertable('sensor_data.monitoramento_audio', 'horario');

-- Cria índices adicionais para acelerar buscas
-- Este índice acelera muito a geração de gráficos e relatórios filtrados por setor e leito
CREATE INDEX idx_monitoramento_setor_leito 
ON sensor_data.monitoramento_audio (setor, leito, horario DESC);

CREATE INDEX idx_monitoramento_mac 
ON sensor_data.monitoramento_audio (mac_address, horario DESC);

SELECT * FROM sensor_data.monitoramento_audio;

-- Apaga a tabela
DROP TABLE sensor_data.monitoramento_audio;

-- Esvazia completamente a tabela de forma instantânea
TRUNCATE TABLE sensor_data.monitoramento_audio;