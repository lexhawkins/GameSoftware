const GRID_SIZE = 6;
const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const revealBtn = document.getElementById("reveal-btn");
const resetBtn = document.getElementById("reset-btn");

let cells = [];
let locked = false;

function buildBoard() {
  boardEl.innerHTML = "";
  cells = [];

  // Fila de encabezado de columnas
  boardEl.appendChild(makeLabel(" "));
  for (let c = 0; c < GRID_SIZE; c++) {
    boardEl.appendChild(makeLabel(String(c + 1)));
  }

  // Filas del tablero
  for (let r = 0; r < GRID_SIZE; r++) {
    boardEl.appendChild(makeLabel(String.fromCharCode(65 + r)));
    const rowButtons = [];
    for (let c = 0; c < GRID_SIZE; c++) {
      const btn = document.createElement("button");
      btn.className = "cell";
      btn.textContent = ".";
      btn.dataset.row = r;
      btn.dataset.col = c;
      btn.addEventListener("click", () => fire(r, c));
      boardEl.appendChild(btn);
      rowButtons.push(btn);
    }
    cells.push(rowButtons);
  }
}

function makeLabel(text) {
  const div = document.createElement("div");
  div.className = "label";
  div.textContent = text;
  return div;
}

function updateBoard(board) {
  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      const btn = cells[r][c];
      const symbol = board[r][c];
      btn.textContent = symbol;
      btn.classList.remove("hit", "miss", "ship");
      if (symbol === "X") btn.classList.add("hit");
      if (symbol === "o") btn.classList.add("miss");
      if (symbol === "S") btn.classList.add("ship");
      if (locked) btn.disabled = true;
      else btn.disabled = symbol === "X" || symbol === "o";
    }
  }
}

async function fire(r, c) {
  if (locked) return;
  const result = await eel.fire_cell(r, c)();
  statusEl.textContent = result.message;
  updateBoard(result.board);
  if (result.done) {
    locked = true;
    updateBoard(result.board);
  }
}

async function loadBoard(reveal = false) {
  const data = await eel.get_board(reveal)();
  updateBoard(data.board);
}

revealBtn.addEventListener("click", async () => {
  const res = await eel.reveal()();
  statusEl.textContent = res.message;
  updateBoard(res.board);
});

resetBtn.addEventListener("click", async () => {
  const res = await eel.reset_game()();
  locked = false;
  statusEl.textContent = res.message;
  updateBoard(res.board);
});

document.addEventListener("DOMContentLoaded", () => {
  buildBoard();
  loadBoard();
});
