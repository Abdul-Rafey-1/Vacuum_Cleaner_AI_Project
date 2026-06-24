
import tkinter as tk
from tkinter import font as tkfont
import random
import time
from collections import deque

# ─────────────────────────── CONSTANTS ───────────────────────────
GRID_SIZE      = 10
CELL_SIZE      = 60
GRID_OFFSET_X  = 20
GRID_OFFSET_Y  = 100
PANEL_W        = 280
CANVAS_W       = GRID_SIZE * CELL_SIZE + GRID_OFFSET_X * 2 + PANEL_W
CANVAS_H       = GRID_SIZE * CELL_SIZE + GRID_OFFSET_Y + 40

# Colour palette
BG_DARK        = "#0f0f1a"
BG_PANEL       = "#1a1a2e"
CELL_CLEAN     = "#1e2a3a"
CELL_DIRTY     = "#3d2200"
CELL_HOVER     = "#1e3a4a"
GRID_LINE      = "#2a3a4a"
DIRT_COLOR     = "#8B4513"
DIRT_DARK      = "#5a2d00"
VAC_BODY       = "#00d4ff"
VAC_ACCENT     = "#0088aa"
VAC_WHEEL      = "#004466"
CLEAN_FLASH    = "#00ff88"
PANEL_BG       = "#16213e"
ACCENT_BLUE    = "#00d4ff"
ACCENT_GREEN   = "#00ff88"
ACCENT_ORANGE  = "#ff8c00"
ACCENT_RED     = "#ff4444"
TEXT_WHITE     = "#ffffff"
TEXT_GREY      = "#8899aa"
BTN_START      = "#00aa66"
BTN_PAUSE      = "#cc8800"
BTN_RESET      = "#aa2244"
BTN_STEP       = "#2255cc"

DIRT_SPAWN_INTERVAL = 40   # steps between random dirt spawns
MAX_DIRT            = 25   # max dirt cells at once
MOVE_DELAY_MS       = 220  # animation speed (ms)


# ─────────────────────────── BFS PATHFINDER ───────────────────────
def bfs(grid, start, targets):
    """Return list of (row,col) steps from start toward nearest target."""
    if not targets:
        return []
    visited = {start}
    queue   = deque([(start, [])])
    while queue:
        (r, c), path = queue.popleft()
        if (r, c) in targets:
            return path + [(r, c)]
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and (nr,nc) not in visited:
                visited.add((nr, nc))
                queue.append(((nr, nc), path + [(nr, nc)]))
    return []


# ─────────────────────────── MAIN APP ─────────────────────────────
class VacuumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Vacuum Cleaner AI – 10×10 Grid")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        # State
        self.grid        = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.vac_r       = 0
        self.vac_c       = 0
        self.path        = []
        self.running     = False
        self.paused      = False
        self.step_count  = 0
        self.cleaned     = 0
        self.spawned     = 0
        self.flash_cells = {}   # (r,c) -> remaining flash frames
        self._after_id   = None
        self.agent_type  = tk.StringVar(value="BFS")

        self._build_ui()
        self._init_dirt(8)
        self._draw_all()

    # ── UI BUILD ──────────────────────────────────────────────────
    def _build_ui(self):
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_W, height=CANVAS_H,
            bg=BG_DARK, highlightthickness=0
        )
        self.canvas.pack()

        # Title
        self.canvas.create_text(
            CANVAS_W // 2 - PANEL_W // 2, 28,
            text="🤖  VACUUM CLEANER AI  SIMULATOR",
            fill=ACCENT_BLUE, font=("Consolas", 17, "bold"), anchor="center"
        )
        self.canvas.create_text(
            CANVAS_W // 2 - PANEL_W // 2, 52,
            text="Intro to Artificial Intelligence  •  10×10 Grid",
            fill=TEXT_GREY, font=("Consolas", 10), anchor="center"
        )

        # Panel background
        px = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 10
        self.canvas.create_rectangle(
            px, GRID_OFFSET_Y,
            px + PANEL_W - 15, GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE,
            fill=PANEL_BG, outline=GRID_LINE, width=1
        )

        # Panel title
        self.canvas.create_text(
            px + (PANEL_W - 15)//2, GRID_OFFSET_Y + 20,
            text="CONTROL PANEL", fill=ACCENT_BLUE,
            font=("Consolas", 11, "bold"), anchor="center"
        )

        # Stat labels (stored for update)
        self._stat_ids = {}
        stats = [
            ("steps",   "Steps",        ACCENT_BLUE),
            ("cleaned", "Cells Cleaned",ACCENT_GREEN),
            ("dirty",   "Dirt Remaining",ACCENT_ORANGE),
            ("spawned", "Total Spawned", TEXT_GREY),
            ("pos",     "Agent Position",TEXT_WHITE),
            ("status",  "Status",        ACCENT_GREEN),
        ]
        sy = GRID_OFFSET_Y + 50
        for key, label, color in stats:
            self.canvas.create_text(
                px + 14, sy, text=label + ":",
                fill=TEXT_GREY, font=("Consolas", 9), anchor="w"
            )
            tid = self.canvas.create_text(
                px + 14, sy + 16, text="—",
                fill=color, font=("Consolas", 13, "bold"), anchor="w"
            )
            self._stat_ids[key] = tid
            sy += 44

        # Agent selector
        sy += 8
        self.canvas.create_text(
            px + 14, sy, text="Agent Strategy:",
            fill=TEXT_GREY, font=("Consolas", 9), anchor="w"
        )
        sy += 18
        for val, label in [("BFS","BFS (Nearest First)"),("RANDOM","Random Walk")]:
            rb = tk.Radiobutton(
                self.root, text=label, variable=self.agent_type, value=val,
                bg=PANEL_BG, fg=TEXT_WHITE, selectcolor=BG_DARK,
                activebackground=PANEL_BG, activeforeground=ACCENT_BLUE,
                font=("Consolas", 9)
            )
            self.canvas.create_window(px + 14, sy, window=rb, anchor="w")
            sy += 20

        # Buttons
        bx = px + 14
        by = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE - 175
        btn_cfg = [
            ("▶  START",  BTN_START,  self.start),
            ("⏸  PAUSE",  BTN_PAUSE,  self.pause),
            ("⟳  RESET",  BTN_RESET,  self.reset),
            ("▷  STEP",   BTN_STEP,   self.step_once),
        ]
        for txt, color, cmd in btn_cfg:
            btn = tk.Button(
                self.root, text=txt, bg=color, fg=TEXT_WHITE,
                activebackground=color, relief="flat",
                font=("Consolas", 10, "bold"),
                width=18, height=1, cursor="hand2", command=cmd
            )
            self.canvas.create_window(bx + 110, by, window=btn)
            by += 38

        # Legend
        ly = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE - 10
        self.canvas.create_text(
            px + 14, ly, text="■ Clean  ■ Dirty  ● Agent",
            fill=TEXT_GREY, font=("Consolas", 8), anchor="w"
        )

        # Speed scale
        self.speed_var = tk.IntVar(value=MOVE_DELAY_MS)
        self.canvas.create_text(
            px + 14, ly + 16, text="Speed (ms/step):",
            fill=TEXT_GREY, font=("Consolas", 8), anchor="w"
        )
        scl = tk.Scale(
            self.root, from_=50, to=800,
            variable=self.speed_var, orient="horizontal",
            bg=PANEL_BG, fg=TEXT_WHITE, troughcolor=BG_DARK,
            highlightthickness=0, length=200, showvalue=True,
            font=("Consolas", 8)
        )
        self.canvas.create_window(px + 115, ly + 38, window=scl)

    # ── GRID INIT ─────────────────────────────────────────────────
    def _init_dirt(self, count=8):
        placed = 0
        while placed < count:
            r = random.randint(0, GRID_SIZE-1)
            c = random.randint(0, GRID_SIZE-1)
            if not self.grid[r][c]:
                self.grid[r][c] = True
                placed += 1
        self.spawned += count

    def _spawn_random_dirt(self):
        dirty_count = sum(self.grid[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE))
        if dirty_count >= MAX_DIRT:
            return
        attempts = 0
        while attempts < 20:
            r = random.randint(0, GRID_SIZE-1)
            c = random.randint(0, GRID_SIZE-1)
            if not self.grid[r][c] and (r, c) != (self.vac_r, self.vac_c):
                self.grid[r][c] = True
                self.spawned += 1
                break
            attempts += 1

    # ── DRAWING ───────────────────────────────────────────────────
    def _cell_xy(self, r, c):
        x = GRID_OFFSET_X + c * CELL_SIZE
        y = GRID_OFFSET_Y + r * CELL_SIZE
        return x, y

    def _draw_all(self):
        self.canvas.delete("grid")
        self._draw_grid()
        self._draw_dirt()
        self._draw_vacuum()
        self._update_stats()

    def _draw_grid(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x, y = self._cell_xy(r, c)
                # Flash effect
                if (r, c) in self.flash_cells:
                    fill = CLEAN_FLASH
                elif self.grid[r][c]:
                    fill = CELL_DIRTY
                else:
                    fill = CELL_CLEAN

                self.canvas.create_rectangle(
                    x+1, y+1, x+CELL_SIZE-1, y+CELL_SIZE-1,
                    fill=fill, outline=GRID_LINE, width=1, tags="grid"
                )
                # Row/col labels
                if c == 0:
                    self.canvas.create_text(
                        GRID_OFFSET_X - 10, y + CELL_SIZE//2,
                        text=str(r), fill=TEXT_GREY,
                        font=("Consolas", 8), anchor="e", tags="grid"
                    )
                if r == 0:
                    self.canvas.create_text(
                        x + CELL_SIZE//2, GRID_OFFSET_Y - 10,
                        text=str(c), fill=TEXT_GREY,
                        font=("Consolas", 8), anchor="s", tags="grid"
                    )

    def _draw_dirt(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and (r, c) not in self.flash_cells:
                    x, y = self._cell_xy(r, c)
                    cx, cy = x + CELL_SIZE//2, y + CELL_SIZE//2
                    # Dirt clumps
                    random.seed(r * 100 + c)
                    for _ in range(6):
                        dx = random.randint(-16, 16)
                        dy = random.randint(-16, 16)
                        size = random.randint(3, 8)
                        self.canvas.create_oval(
                            cx+dx-size, cy+dy-size,
                            cx+dx+size, cy+dy+size,
                            fill=DIRT_COLOR, outline=DIRT_DARK, width=1, tags="grid"
                        )
                    random.seed()

    def _draw_vacuum(self):
        r, c = self.vac_r, self.vac_c
        x, y = self._cell_xy(r, c)
        cx, cy = x + CELL_SIZE//2, y + CELL_SIZE//2
        pad = 6

        # Shadow
        self.canvas.create_oval(
            cx-18, cy+12, cx+18, cy+18,
            fill="#000033", outline="", tags="grid"
        )
        # Body
        self.canvas.create_oval(
            x+pad, y+pad, x+CELL_SIZE-pad, y+CELL_SIZE-pad,
            fill=VAC_BODY, outline=VAC_ACCENT, width=2, tags="grid"
        )
        # Inner circle
        self.canvas.create_oval(
            cx-10, cy-10, cx+10, cy+10,
            fill=VAC_ACCENT, outline="", tags="grid"
        )
        # Eyes
        self.canvas.create_oval(cx-7, cy-6, cx-3, cy-2, fill="white", outline="", tags="grid")
        self.canvas.create_oval(cx+3, cy-6, cx+7, cy-2, fill="white", outline="", tags="grid")
        self.canvas.create_oval(cx-6, cy-5, cx-4, cy-3, fill="#001133", outline="", tags="grid")
        self.canvas.create_oval(cx+4, cy-5, cx+6, cy-3, fill="#001133", outline="", tags="grid")
        # Wheels
        for wx in [cx-14, cx+10]:
            self.canvas.create_rectangle(
                wx, cy+8, wx+8, cy+14,
                fill=VAC_WHEEL, outline="", tags="grid"
            )
        # Antenna
        self.canvas.create_line(cx, cy-CELL_SIZE//2+pad, cx, cy-14, fill=ACCENT_BLUE, width=2, tags="grid")
        self.canvas.create_oval(cx-3, cy-CELL_SIZE//2+pad-3, cx+3, cy-CELL_SIZE//2+pad+3,
                                fill=ACCENT_BLUE, outline="", tags="grid")

    def _update_stats(self):
        dirty = sum(self.grid[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE))
        status = "RUNNING" if self.running and not self.paused else ("PAUSED" if self.paused else "IDLE")
        color_map = {"RUNNING": ACCENT_GREEN, "PAUSED": ACCENT_ORANGE, "IDLE": TEXT_GREY}
        values = {
            "steps":   str(self.step_count),
            "cleaned": str(self.cleaned),
            "dirty":   str(dirty),
            "spawned": str(self.spawned),
            "pos":     f"({self.vac_r}, {self.vac_c})",
            "status":  status,
        }
        for key, val in values.items():
            self.canvas.itemconfig(self._stat_ids[key], text=val)
        self.canvas.itemconfig(self._stat_ids["status"],
                               fill=color_map.get(status, TEXT_WHITE))

    # ── AI AGENTS ─────────────────────────────────────────────────
    def _get_next_move_bfs(self):
        dirty = {(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.grid[r][c]}
        if not dirty:
            return None
        if self.path:
            # Verify current path still leads to dirt
            dest = self.path[-1]
            if dest in dirty:
                return self.path.pop(0)
            else:
                self.path = []
        path = bfs(self.grid, (self.vac_r, self.vac_c), dirty)
        if path:
            self.path = path
            return self.path.pop(0)
        return None

    def _get_next_move_random(self):
        dirty = {(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.grid[r][c]}
        if not dirty:
            return None
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = self.vac_r+dr, self.vac_c+dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                neighbors.append((nr, nc))
        # Prefer dirty
        dirty_nb = [n for n in neighbors if n in dirty]
        return random.choice(dirty_nb if dirty_nb else neighbors)

    # ── SIMULATION STEP ───────────────────────────────────────────
    def _do_step(self):
        # Spawn dirt dynamically
        if self.step_count > 0 and self.step_count % DIRT_SPAWN_INTERVAL == 0:
            self._spawn_random_dirt()

        # Decay flash cells
        to_remove = [k for k, v in self.flash_cells.items() if v <= 0]
        for k in to_remove:
            del self.flash_cells[k]
        for k in self.flash_cells:
            self.flash_cells[k] -= 1

        # Move agent
        if self.agent_type.get() == "BFS":
            move = self._get_next_move_bfs()
        else:
            move = self._get_next_move_random()

        if move:
            self.vac_r, self.vac_c = move

        self.step_count += 1

        # Clean current cell
        if self.grid[self.vac_r][self.vac_c]:
            self.grid[self.vac_r][self.vac_c] = False
            self.cleaned += 1
            self.flash_cells[(self.vac_r, self.vac_c)] = 3
            self.path = []   # recompute path after clean

        self._draw_all()

        if self.running and not self.paused:
            self._after_id = self.root.after(self.speed_var.get(), self._do_step)

    # ── CONTROLS ──────────────────────────────────────────────────
    def start(self):
        if self.running and not self.paused:
            return
        if self.paused:
            self.paused = False
        else:
            self.running = True
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._do_step()

    def pause(self):
        if self.running:
            self.paused = not self.paused
            if not self.paused:
                self._do_step()
            self._update_stats()

    def reset(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.running  = False
        self.paused   = False
        self.grid     = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.vac_r    = 0
        self.vac_c    = 0
        self.path     = []
        self.step_count = 0
        self.cleaned  = 0
        self.spawned  = 0
        self.flash_cells = {}
        self._init_dirt(8)
        self._draw_all()

    def step_once(self):
        if not self.running:
            self.running = True
            self.paused  = True
        self._do_step()
        self.running = False
        self.paused  = False
        self._update_stats()


# ─────────────────────────── ENTRY POINT ──────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    app  = VacuumApp(root)
    root.mainloop()
