"""
Battleship 6x6 con interfaz en Eel.
Requiere: pip install eel
Ejecuta: python main.py
"""

from pathlib import Path

import eel

# Configuracion del tablero
GRID_SIZE = 6
EMPTY, SHIP, HIT, MISS = ".", "S", "X", "o"
SHIP_CELLS = {(1, 1), (1, 2)}  # Barco de prueba B2-B3

# Estado global simple para esta demo
board = []


def create_board(size=GRID_SIZE):
    return [[EMPTY for _ in range(size)] for _ in range(size)]


def reset_board():
    global board
    board = create_board()
    for r, c in SHIP_CELLS:
        board[r][c] = SHIP


def render_for_frontend(reveal=False):
    """Devuelve una vista del tablero sin mostrar barcos ocultos por defecto."""
    view = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            value = board[r][c]
            if value == SHIP and not reveal:
                row.append(EMPTY)
            else:
                row.append(value)
        view.append(row)
    return view


def shoot(r, c):
    if board[r][c] == SHIP:
        board[r][c] = HIT
        return True
    if board[r][c] == EMPTY:
        board[r][c] = MISS
    return False


def all_sunk():
    return all(cell != SHIP for row in board for cell in row)


@eel.expose
def get_board(reveal=False):
    return {"board": render_for_frontend(reveal=reveal)}


@eel.expose
def fire_cell(r, c):
    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
        return {
            "ok": False,
            "message": "Fuera del tablero.",
            "board": render_for_frontend(),
        }

    current = board[r][c]
    if current in (HIT, MISS):
        return {
            "ok": False,
            "message": "Ya tiraste ahi.",
            "board": render_for_frontend(),
        }

    hit = shoot(r, c)
    message = "Tocado." if hit else "Agua."
    done = all_sunk()
    if done:
        message = "Hundiste el barco de prueba."
    return {
        "ok": True,
        "hit": hit,
        "done": done,
        "message": message,
        "board": render_for_frontend(),
    }


@eel.expose
def reveal():
    return {"board": render_for_frontend(reveal=True), "message": "Barcos revelados."}


@eel.expose
def reset_game():
    reset_board()
    return {"board": render_for_frontend(), "message": "Juego reiniciado."}


def main():
    reset_board()
    web_dir = Path(__file__).parent / "web"
    eel.init(str(web_dir))
    eel.start("index.html", size=(520, 680), block=True)


if __name__ == "__main__":
    main()
