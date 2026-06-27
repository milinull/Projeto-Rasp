class CiclosAudio:
    """
    Classe responsável por processar o volume do áudio ciclo a ciclo,
    identificando se alguém está falando, pausado, ou falando muito alto.
    """

    def __init__(
        self,
        limite_volume_fala: float = 12.0,
        limite_fala_alta: float = 42.0,
        janela_fala_alta_segundos: float = 3.0,
        acertos_para_fala_alta: int = 15,
        tempo_para_ativar_fala: float = 1.5,
        tempo_para_desligar_fala: float = 1.0,
        limite_pico_rapido: float = 40.0,
    ) -> None:
        """
        Inicializa os parâmetros de sensibilidade de áudio e os
        contadores internos de tempo (assumindo ciclos de 0.03 segundos).
        """
        # Limites de volume
        self.limite_volume_fala = limite_volume_fala
        self.limite_fala_alta = limite_fala_alta
        self.limite_pico_rapido = limite_pico_rapido
        self.acertos_para_fala_alta = acertos_para_fala_alta

        # Conversão de tempo em segundos para quantidade de ciclos (ex: 0.03s por ciclo)
        self.ciclos_para_falar = int(tempo_para_ativar_fala / 0.03)
        self.ciclos_para_pausa = int(tempo_para_desligar_fala / 0.03)
        self.ciclos_confirmar_fim_som = 15
        self.tamanho_janela_ciclos = int(janela_fala_alta_segundos / 0.03)
        self.ciclos_delay_fala_alta = int(2.0 / 0.03)

        # Variáveis de controle de estado e histórico
        self.ciclo_global = 0
        self.historico_picos_altos = []
        self.fala_alta_timer = 0
        self.som_ativo = False
        self.falando = False
        self.ciclos_som_atual = 0
        self.ciclos_silencio = 0
        self.pico_max_volume = 0.0
        self.estado_atual = "       "
        self.pico_timer = 0

        # Estado da cor que será enviada para o WebSocket
        self.estado_websocket = "green"

    def processar(self, volume_real: float) -> str:
        """
        Recebe o volume atual do áudio, atualiza os contadores internos,
        define se está ocorrendo uma fala (ou grito/pico) e ajusta as cores.
        Retorna o texto do estado atual para exibição (ex: "FALANDO", "PICO").
        """
        self.ciclo_global += 1

        # Limpeza visual do aviso de PICO no terminal após o tempo acabar
        if self.pico_timer > 0:
            self.pico_timer -= 1
            if self.pico_timer == 0 and not self.falando:
                self.estado_atual = "       "

        # Lógica principal: Verifica se o som atual ultrapassou o limite de fala
        if volume_real >= self.limite_volume_fala:
            self.som_ativo = True
            self.ciclos_som_atual += 1
            self.ciclos_silencio = 0
            self.pico_max_volume = max(self.pico_max_volume, volume_real)

            # Se manteve o som tempo suficiente, muda o estado para "FALANDO"
            if not self.falando and self.ciclos_som_atual >= self.ciclos_para_falar:
                self.falando = True
                self.estado_atual = "FALANDO"
                self.pico_timer = 0
        else:
            # Lógica para quando o som está abaixo do limite (silêncio)
            if self.som_ativo:
                self.ciclos_silencio += 1

                if self.falando:
                    # Se estava falando e ficou em silêncio tempo suficiente, encerra a fala
                    if self.ciclos_silencio >= self.ciclos_para_pausa:
                        self.falando = False
                        self.som_ativo = False
                        self.estado_atual = "       "
                        self.ciclos_som_atual = 0
                        self.pico_max_volume = 0.0
                else:
                    # Se não estava falando oficialmente, mas houve um som rápido e alto (PICO)
                    if self.ciclos_silencio >= self.ciclos_confirmar_fim_som:
                        if self.pico_max_volume >= self.limite_pico_rapido:
                            self.estado_atual = "PICO   "
                            self.pico_timer = 40

                        # Reseta os controles de som
                        self.som_ativo = False
                        self.ciclos_som_atual = 0
                        self.pico_max_volume = 0.0

        # Registra os momentos em que a fala foi muito alta
        if self.falando and volume_real >= self.limite_fala_alta:
            self.historico_picos_altos.append(self.ciclo_global)

        # Remove picos antigos do histórico (mantém apenas a janela de tempo recente)
        limite_idade = self.ciclo_global - self.tamanho_janela_ciclos
        self.historico_picos_altos = [
            c for c in self.historico_picos_altos if c > limite_idade
        ]

        # Se houver muitos picos altos recentes, aciona o timer de fala alta
        if len(self.historico_picos_altos) >= self.acertos_para_fala_alta:
            self.fala_alta_timer = self.ciclos_delay_fala_alta
            # Remove metade dos picos antigos para não reativar instantaneamente
            self.historico_picos_altos = self.historico_picos_altos[
                self.acertos_para_fala_alta // 2 :
            ]

        # Define a cor do estado para o WebSocket baseado no que está acontecendo
        if self.falando:
            if self.fala_alta_timer > 0:
                self.estado_websocket = "red"  # Falando muito alto
                self.fala_alta_timer -= 1
            else:
                self.estado_websocket = "yellow"  # Falando em volume normal
        else:
            self.estado_websocket = "green"  # Silêncio / Aguardando
            self.fala_alta_timer = 0
            self.historico_picos_altos.clear()

        return self.estado_atual
