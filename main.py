"""Battleship 6x6 - backend using eel for UI.

Player vs Bot (Evil Gari). Player places 3 ships (lengths 3,2,4) with orientation.
Bot places ships randomly. Frontend uses eel to call the exposed functions.

Run: pip install eel
Then: python main.py
"""

from pathlib import Path
import random
import eel

# Configuration
GRID_SIZE = 6
EMPTY, SHIP, HIT, MISS = ".", "S", "X", "o"
PLAYER_SHIP_SIZES = [3, 2, 4]


class Board:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.ships = []  # list of ship cells sets

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def can_place(self, r, c, length, horizontal):
        cells = []
        for i in range(length):
            rr = r
            cc = c + i if horizontal else c
            rr = r if horizontal else r + i
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
            rr = r
            cc = c + i if horizontal else c
            rr = r if horizontal else r + i
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
        else:
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
        self.phase = "placement"  # or "playing" or "over"
        self.next_ship_idx = 0
        self.bot_known_shots = set()
        self.bot_possible_shots = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        random.shuffle(self.bot_possible_shots)

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
                # If failed terribly, reset and restart
                self.bot = Board()
                return self.bot_place_ships_random()

    def place_player_ship(self, r, c, horizontal):
        if self.phase != "placement":
            return {"ok": False, "message": "No en fase de colocación."}
        if self.next_ship_idx >= len(PLAYER_SHIP_SIZES):
            return {"ok": False, "message": "Ya colocaste todas las naves."}
        length = PLAYER_SHIP_SIZES[self.next_ship_idx]
        ok = self.player.place_ship(r, c, length, horizontal)
        if not ok:
            return {"ok": False, "message": "No se puede colocar ahí."}
        self.next_ship_idx += 1
        if self.next_ship_idx >= len(PLAYER_SHIP_SIZES):
            self.phase = "playing"
        return {"ok": True, "message": "Barco colocado.", "next": self.next_ship_idx}

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
            res["message"] = "¡Ganaste! Hundiste todos los barcos del bot."
        else:
            # bot turn: single shot
            br, bc = self.bot_take_shot()
            bot_res = self.player.receive_shot(br, bc)
            bot_done = self.player.all_sunk()
            if bot_done:
                self.phase = "over"
                res["bot_done"] = True
                res["message"] = "El bot hundió todos tus barcos. Perdiste."
            res["bot_shot"] = {"r": br, "c": bc, **bot_res}
        return res

    def bot_take_shot(self):
        # Simple random bot that avoids shooting the same cell twice
        while self.bot_possible_shots:
            r, c = self.bot_possible_shots.pop()
            if (r, c) in self.bot_known_shots:
                continue
            self.bot_known_shots.add((r, c))
            return r, c
        # fallback (shouldn't happen)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (r, c) not in self.bot_known_shots:
                    self.bot_known_shots.add((r, c))
                    return r, c


GAME = Game()


@eel.expose
def start_new_game():
    GAME.reset()
    GAME.bot_place_ships_random()
    return get_state()


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
    GAME.bot_place_ships_random()
    return get_state()


def main():
    web_dir = Path(__file__).parent / "web"
    eel.init(str(web_dir))
    # non-blocking to allow debugging; eel will open the UI
    eel.start("index.html", size=(900, 700), block=True)


if __name__ == "__main__":
    main()
