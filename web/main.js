const GRID_SIZE = 6;

const playerBoardEl = document.getElementById("player-board");
const botBoardEl = document.getElementById("bot-board");
const statusEl = document.getElementById("status");
const revealBtn = document.getElementById("reveal-btn");
const resetBtn = document.getElementById("reset-btn");
const startBtn = document.getElementById("start-btn");
const shipSizeEl = document.getElementById("ship-size");

let playerCells = [];
let botCells = [];
let state = null;

function makeGrid(container, allowLabels = true) {
  container.innerHTML = "";
  const cells = [];

  // header
  for (let c = -1; c < GRID_SIZE; c++) {
    const label = document.createElement("div");
    label.className = "label";
    label.textContent = c >= 0 ? String(c + 1) : "";
    container.appendChild(label);
  }

  for (let r = 0; r < GRID_SIZE; r++) {
    const rowLabel = document.createElement("div");
    rowLabel.className = "label";
    rowLabel.textContent = String.fromCharCode(65 + r);
    container.appendChild(rowLabel);
    const row = [];
    for (let c = 0; c < GRID_SIZE; c++) {
      const btn = document.createElement("button");
      btn.className = "cell";
      btn.textContent = ".";
      btn.dataset.row = r;
      btn.dataset.col = c;
      container.appendChild(btn);
      row.push(btn);
    }
    cells.push(row);
  }
  return cells;
}

function buildBoards() {
  playerCells = makeGrid(playerBoardEl);
  botCells = makeGrid(botBoardEl);
}

function clearCellClasses() {
  [playerCells, botCells].forEach(grid => {
    grid.forEach(row => row.forEach(btn => btn.className = 'cell'));
  });
}

function updateBoards() {
  if (!state) return;
  clearCellClasses();
  const p = state.player_board;
  const b = state.bot_board;

  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      const pb = playerCells[r][c];
      const symbolP = p[r][c];
      pb.textContent = symbolP;
      pb.classList.remove("hit", "miss", "ship");
      if (symbolP === "X") pb.classList.add("hit");
      if (symbolP === "o") pb.classList.add("miss");
      if (symbolP === "S") pb.classList.add("ship");

      const bb = botCells[r][c];
      const symbolB = b[r][c];
      bb.textContent = symbolB;
      bb.classList.remove("hit", "miss", "ship");
      if (symbolB === "X") bb.classList.add("hit");
      if (symbolB === "o") bb.classList.add("miss");
      if (symbolB === "S") bb.classList.add("ship");
    }
  }

  // update placement info
  if (state.phase === 'placement') {
    const idx = state.next_ship_idx || 0;
    const sizes = state.ship_sizes || [];
    shipSizeEl.textContent = sizes[idx] || '-';
    statusEl.textContent = 'Coloca tus naves: haz clic en tu tablero.';
  } else if (state.phase === 'playing') {
    shipSizeEl.textContent = '-';
    statusEl.textContent = 'Turno de disparo: haz clic en el tablero del bot.';
  } else if (state.phase === 'over') {
    statusEl.textContent = 'Juego terminado.';
  }
}

function getOrientation() {
  const el = document.querySelector('input[name="orientation"]:checked');
  return el ? el.value === 'H' : true;
}

async function refreshState() {
  state = await eel.get_state()();
  updateBoards();
}

playerBoardEl.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('.cell');
  if (!btn) return;
  const r = Number(btn.dataset.row);
  const c = Number(btn.dataset.col);
  if (!state) return;
  if (state.phase !== 'placement') return;
  const horizontal = getOrientation();
  const res = await eel.place_player_ship(r, c, horizontal)();
  state = res;
  if (res.ok === false) {
    statusEl.textContent = res.message || 'No se pudo colocar.';
  } else {
    statusEl.textContent = res.message || 'Barco colocado.';
  }
  updateBoards();
});

botBoardEl.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('.cell');
  if (!btn) return;
  const r = Number(btn.dataset.row);
  const c = Number(btn.dataset.col);
  if (!state) return;
  if (state.phase !== 'playing') return;
  const res = await eel.player_fire(r, c)();
  state = res;
  if (res.ok === false) {
    statusEl.textContent = res.message || 'Movimiento inválido.';
  } else {
    statusEl.textContent = res.message || 'Disparo realizado.';
    if (res.bot_shot) {
      // show bot shot message too
      statusEl.textContent += ` Bot disparó en ${String.fromCharCode(65 + res.bot_shot.r)}${res.bot_shot.c + 1}: ${res.bot_shot.message}`;
    }
  }
  updateBoards();
});

revealBtn.addEventListener('click', async () => {
  const res = await eel.reveal_boards()();
  if (res) {
    // update both boards revealed
    if (res.player_board) state.player_board = res.player_board;
    if (res.bot_board) state.bot_board = res.bot_board;
    statusEl.textContent = res.message || 'Revelado.';
    updateBoards();
  }
});

resetBtn.addEventListener('click', async () => {
  const res = await eel.reset_game()();
  state = res;
  statusEl.textContent = 'Juego reiniciado.';
  updateBoards();
});

startBtn.addEventListener('click', async () => {
  const res = await eel.start_new_game()();
  state = res;
  statusEl.textContent = 'Nueva partida iniciada. Coloca tus barcos.';
  updateBoards();
});

document.addEventListener('DOMContentLoaded', async () => {
  buildBoards();
  await refreshState();
});
