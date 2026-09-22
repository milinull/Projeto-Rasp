// Dicionário adaptado para refletir o nível de voz na interface
const states = {
  red: { title: "ALERTA", message: "FALA ALTA" },
  yellow: { title: "MONITORAMENTO", message: "CONVERSA" },
  green: { title: "ESTÁVEL", message: "SILÊNCIO" },
};

function setStatus(color) {
  const card = document.getElementById("status-card");
  const title = document.getElementById("status-title");
  const message = document.getElementById("status-message");

  // Atualiza a classe do cartão para acionar o CSS correspondente
  card.className = `status-card card-${color}`;

  // Atualiza os textos baseado no dicionário 'states'
  title.textContent = states[color].title;
  message.textContent = states[color].message;
}

function updateClock() {
  const now = new Date();
  // Garante que horas, minutos e segundos tenham sempre 2 dígitos
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");

  document.getElementById("clock").textContent = `${hh}:${mm}:${ss}`;
}

// Configura o relógio para atualizar a cada 1 segundo
setInterval(updateClock, 1000);
updateClock();

// ==========================================
// LÓGICA DO MODAL & COMANDOS
// ==========================================
const btnSettings = document.getElementById("btn-settings");
const btnCloseSettings = document.getElementById("btn-close-settings");
const modalOverlay = document.getElementById("settings-modal");

const micSelect = document.getElementById("mic-select");

const gainSlider = document.getElementById("gain-slider");
const gainValue = document.getElementById("gain-value");

// Envia o novo ganho em tempo real ao mover a barra
gainSlider.addEventListener("input", (e) => {
  const value = e.target.value;
  gainValue.textContent = value > 0 ? `+${value}` : value;

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(
      JSON.stringify({ comando: "alterar_ganho", valor: parseInt(value) }),
    );
  }
});

// Modifica o evento do select para resetar o ganho ao trocar de microfone
micSelect.addEventListener("change", (e) => {
  if (e.target.value !== "" && ws && ws.readyState === WebSocket.OPEN) {
    // Envia o comando do novo mic
    ws.send(
      JSON.stringify({
        comando: "trocar_microfone",
        id: parseInt(e.target.value),
      }),
    );

    // Força a barra de ganho a voltar para o zero
    gainSlider.value = 0;
    gainValue.textContent = "0";
    ws.send(JSON.stringify({ comando: "alterar_ganho", valor: 0 }));
  }
});

let ws; // Variável global para o WebSocket

btnSettings.addEventListener("click", () => {
  btnSettings.classList.add("spin");
  setTimeout(() => {
    btnSettings.classList.remove("spin");
  }, 500);
  modalOverlay.classList.add("active");

  // Solicita a lista de microfones ao Python via WebSocket
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ comando: "listar_microfones" }));
  }
});

btnCloseSettings.addEventListener("click", () => {
  modalOverlay.classList.remove("active");
});

modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) {
    modalOverlay.classList.remove("active");
  }
});

// ==========================================
// CONEXÃO WEBSOCKET
// ==========================================
function connectWebSocket() {
  const wsDot = document.getElementById("ws-dot");
  const wsText = document.getElementById("ws-text");
  ws = new WebSocket("ws://localhost:8765");

  ws.onopen = () => {
    wsDot.classList.add("connected");
    wsText.textContent = "Conectado";
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Atualiza os painéis centrais
    if (data.estado) {
      setStatus(data.estado);
    }

    // Move a barra de volume do menu simulando o teste_mic.py
    if (data.volume !== undefined) {
      const volumeBar = document.getElementById("volume-bar");

      // Transforma o teto de 50 (do terminal) em 100% da barra do HTML
      const percentual = (data.volume / 50) * 100;
      const barWidth = Math.min(percentual, 100);

      volumeBar.style.width = `${barWidth}%`;

      if (data.estado === "red") volumeBar.style.backgroundColor = "#ef4444";
      else if (data.estado === "yellow")
        volumeBar.style.backgroundColor = "#f59e0b";
      else volumeBar.style.backgroundColor = "#10b981";
    }

    // Preenche o Select com a lista vinda do dispositivos.py
    if (data.microfones) {
      const select = document.getElementById("mic-select");
      select.innerHTML = '<option value="">Selecione um microfone...</option>';
      data.microfones.forEach((mic) => {
        select.innerHTML += `<option value="${mic.id}">[${mic.id}] ${mic.nome}</option>`;
      });
    }
  };

  ws.onclose = () => {
    wsDot.classList.remove("connected");
    wsText.textContent = "Tentando reconectar...";
    setStatus("green");
    setTimeout(connectWebSocket, 3000);
  };
}

connectWebSocket();
