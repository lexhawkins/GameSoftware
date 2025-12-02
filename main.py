"""
Battleship 6x6 - backend usando Eel para la UI.
Jugador vs Bot (Evil Gari). El jugador coloca 3 barcos (largos 3,2,4).
El bot coloca sus barcos al azar. La UI llama a las funciones expuestas.

Requiere: pip install eel
Ejecuta: python main.py
"""

from pathlib import Path
import random
import eel

# Configuracion
GRID_SIZE = 6
EMPTY, SHIP, HIT, MISS = ".", "S", "X", "o"
PLAYER_SHIP_SIZES = [3, 2, 4]


class Board:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.ships = []  # lista de sets de celdas

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def can_place(self, r, c, length, horizontal):
        cells = []
        for i in range(length):
            rr = r if horizontal else r + i
            cc = c + i if horizontal else c
            if not self.in_bounds(rr, cc):
                return False
            if self.grid[rr][cc] == SHIP:
                return False
            cells.append((rr, cc))
        return True

    def place_ship(self, r, c, length, horizontal):
        if not self.can_place(r, c, length, horizontal):
            return False
        placed = set()
        for i in range(length):
            rr = r if horizontal else r + i
            cc = c + i if horizontal else c
            self.grid[rr][cc] = SHIP
            placed.add((rr, cc))
        self.ships.append(placed)
        return True

    def receive_shot(self, r, c):
        if not self.in_bounds(r, c):
            return {"ok": False, "message": "Fuera del tablero."}
        cur = self.grid[r][c]
        if cur in (HIT, MISS):
            return {"ok": False, "message": "Ya disparaste ahi."}
        if cur == SHIP:
            self.grid[r][c] = HIT
            return {"ok": True, "hit": True, "message": "Tocado."}
        self.grid[r][c] = MISS
        return {"ok": True, "hit": False, "message": "Agua."}

    def all_sunk(self):
        return all(cell != SHIP for row in self.grid for cell in row)

    def view(self, reveal=False):
        view = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                v = self.grid[r][c]
                if v == SHIP and not reveal:
                    row.append(EMPTY)
                else:
                    row.append(v)
            view.append(row)
        return view


class Game:
    def __init__(self):
        self.player = Board()
        self.bot = Board()
        self.phase = "placement"  # placement | playing | over
        self.next_ship_idx = 0
        self.bot_known_shots = set()
        self.bot_possible_shots = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(self.bot_possible_shots)
        # Aseguramos que el bot tenga barcos desde el inicio
        self.bot_place_ships_random()

    def reset(self):
        self.__init__()

    def bot_place_ships_random(self):
        for length in PLAYER_SHIP_SIZES:
            placed = False
            attempts = 0
            while not placed and attempts < 200:
                horizontal = random.choice([True, False])
                r = random.randrange(GRID_SIZE)
                c = random.randrange(GRID_SIZE)
                placed = self.bot.place_ship(r, c, length, horizontal)
                attempts += 1
            if not placed:
                self.bot = Board()
                return self.bot_place_ships_random()

    def place_player_ship(self, r, c, horizontal):
        if self.phase != "placement":
            return {"ok": False, "message": "No en fase de colocacion."}
        if self.next_ship_idx >= len(PLAYER_SHIP_SIZES):
            return {"ok": False, "message": "Ya colocaste todas las naves."}
        length = PLAYER_SHIP_SIZES[self.next_ship_idx]
        ok = self.player.place_ship(r, c, length, horizontal)
        if not ok:
            return {"ok": False, "message": "No se puede colocar ahi."}
        self.next_ship_idx += 1
        message = "Barco colocado."
        if self.next_ship_idx >= len(PLAYER_SHIP_SIZES):
            message = "Barcos colocados. Pulsa Iniciar para jugar."
        return {"ok": True, "message": message, "next": self.next_ship_idx}

    def start_battle(self):
        if self.phase != "placement":
            return {"ok": False, "message": "Ya fue iniciado o terminado."}
        if self.next_ship_idx < len(PLAYER_SHIP_SIZES):
            return {"ok": False, "message": "Coloca todas tus naves antes de iniciar."}
        self.phase = "playing"
        return {"ok": True, "message": "Comienza la batalla. Dispara al bot."}

    def player_fire(self, r, c):
        if self.phase != "playing":
            return {"ok": False, "message": "No en fase de juego."}
        res = self.bot.receive_shot(r, c)
        if not res.get("ok"):
            return res
        done = self.bot.all_sunk()
        if done:
            self.phase = "over"
            res["done"] = True
            res["message"] = "Ganaste. Hundiste todos los barcos del bot."
        else:
            br, bc = self.bot_take_shot()
            bot_res = self.player.receive_shot(br, bc)
            bot_done = self.player.all_sunk()
            if bot_done:
                self.phase = "over"
                res["bot_done"] = True
                res["message"] = "El bot hundio todos tus barcos. Perdiste."
            res["bot_shot"] = {"r": br, "c": bc, **bot_res}
        return res

    def bot_take_shot(self):
        while self.bot_possible_shots:
            r, c = self.bot_possible_shots.pop()
            if (r, c) in self.bot_known_shots:
                continue
            self.bot_known_shots.add((r, c))
            return r, c
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (r, c) not in self.bot_known_shots:
                    self.bot_known_shots.add((r, c))
                    return r, c


GAME = Game()


@eel.expose
def start_new_game():
    GAME.reset()
    return get_state()


@eel.expose
def start_battle():
    res = GAME.start_battle()
    state = get_state()
    state.update(res)
    return state


@eel.expose
def get_state():
    return {
        "phase": GAME.phase,
        "player_board": GAME.player.view(reveal=True),
        "bot_board": GAME.bot.view(reveal=False),
        "next_ship_idx": GAME.next_ship_idx,
        "ship_sizes": PLAYER_SHIP_SIZES,
    }


@eel.expose
def place_player_ship(r, c, horizontal):
    res = GAME.place_player_ship(r, c, horizontal)
    state = get_state()
    state.update(res)
    return state


@eel.expose
def player_fire(r, c):
    res = GAME.player_fire(r, c)
    state = get_state()
    state.update(res)
    return state


@eel.expose
def reveal_boards():
    return {
        "player_board": GAME.player.view(reveal=True),
        "bot_board": GAME.bot.view(reveal=True),
        "message": "Tableros revelados.",
    }


@eel.expose
def reset_game():
    GAME.reset()
    return get_state()


def main():
    web_dir = Path(__file__).parent / "web"
    eel.init(str(web_dir))
    eel.start("index.html", size=(900, 700), block=True)


if __name__ == "__main__":
    main()
