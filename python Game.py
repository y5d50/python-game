"""
Created on Wed Oct 29 14:41:36 2025
CourseWork for CSC-44102-2025-SEM1-A
@author: John Hamlyn 2201387701

Survival Game using Tkinter with Boss Stage (Player collision with boss attacks)

Acknowledgment:
This project has benefited from the use of AI assistance (OpenAI's ChatGPT)
for code optimization, debugging, and providing guidance on structuring 
game logic, event handling, and implementing boss mechanics.
"""

import tkinter as tk
import random
import time
import math

# --- Game Configuration ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PLAYER_SIZE = 30
ENEMY_SIZE = 25
PLAYER_SPEED = 6
ENEMY_SPEED = PLAYER_SPEED * 1.15
ENEMY_SPAWN_INTERVAL = 10000
ENEMY_LIFETIME = 9500
LEVEL_UP_INTERVAL = 20000
POINTS_PER_SECOND = 10

# --- Boss Configuration ---
BOSS_SIZE = 100
WARNING_COLOR = "#ff9999"  # lighter red for harmless warning
BOSS_COLOR = "red"
BOSS_ATTACK_INTERVAL = 200  # ms per attack step
SMALL_ENEMY_SIZE = 25

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Survival Game")
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="black")
        self.canvas.pack()

        # Game state
        self.running = False
        self.active_timers = []
        self.keys_pressed = set()
        self.enemies = []

        # Boss state
        self.boss_warning = None
        self.boss = None
        self.boss_attack_running = False
        self.attack_squares = []

        # Menu
        self.menu_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
            text="Click to Play",
            fill="white", font=("Arial", 36, "bold")
        )
        self.canvas.bind("<Button-1>", self.start_game)

    # --- Timer management ---
    def cancel_all_timers(self):
        for timer_id in self.active_timers:
            self.root.after_cancel(timer_id)
        self.active_timers.clear()

    def add_timer(self, func, delay):
        timer_id = self.root.after(delay, func)
        self.active_timers.append(timer_id)
        return timer_id

    # --- Game start ---
    def start_game(self, event=None):
        if self.running:
            return
        self.cancel_all_timers()
        self.canvas.delete("all")

        # Player
        self.player_x = WINDOW_WIDTH // 2
        self.player_y = WINDOW_HEIGHT // 2
        self.player = self.canvas.create_rectangle(
            self.player_x - PLAYER_SIZE//2, self.player_y - PLAYER_SIZE//2,
            self.player_x + PLAYER_SIZE//2, self.player_y + PLAYER_SIZE//2,
            fill="cyan"
        )

        # Timer
        self.start_time = time.time()
        self.timer_text = self.canvas.create_text(
            10, 10, anchor="nw", fill="white", font=("Arial",16), text="Time:0"
        )

        # Enemies
        self.enemies = []
        self.enemy_min = 3
        self.enemy_max = 6

        # Boss
        self.boss_warning = None
        self.boss = None
        self.boss_attack_running = False
        self.attack_squares = []

        self.running = True
        self.keys_pressed.clear()

        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

        # Loops
        self.add_timer(self.update_timer, 1000)
        self.update_player_position()
        self.spawn_enemies()
        self.move_enemies()
        self.add_timer(self.level_up, LEVEL_UP_INTERVAL)
        self.check_collision()

    # --- Player controls ---
    def key_press(self, event):
        if not self.running: return
        self.keys_pressed.add(event.keysym.lower())

    def key_release(self, event):
        if event.keysym.lower() in self.keys_pressed:
            self.keys_pressed.remove(event.keysym.lower())

    def update_player_position(self):
        if not self.running: return
        if 'w' in self.keys_pressed: self.player_y -= PLAYER_SPEED
        if 's' in self.keys_pressed: self.player_y += PLAYER_SPEED
        if 'a' in self.keys_pressed: self.player_x -= PLAYER_SPEED
        if 'd' in self.keys_pressed: self.player_x += PLAYER_SPEED

        self.player_x = max(PLAYER_SIZE//2, min(WINDOW_WIDTH - PLAYER_SIZE//2, self.player_x))
        self.player_y = max(PLAYER_SIZE//2, min(WINDOW_HEIGHT - PLAYER_SIZE//2, self.player_y))

        self.canvas.coords(
            self.player,
            self.player_x - PLAYER_SIZE//2, self.player_y - PLAYER_SIZE//2,
            self.player_x + PLAYER_SIZE//2, self.player_y + PLAYER_SIZE//2
        )
        self.add_timer(self.update_player_position, 20)

    # --- Game timer and boss scheduling ---
    def update_timer(self):
        if not self.running: return
        elapsed = int(time.time() - self.start_time)
        self.canvas.itemconfig(self.timer_text, text=f"Time: {elapsed}")

        if elapsed % 30 == 29: self.start_boss_warning()
        elif elapsed % 30 == 0 and elapsed > 0: self.spawn_boss()

        self.add_timer(self.update_timer, 1000)

    # --- Boss warning ---
    def start_boss_warning(self):
        if self.boss_warning: return
        for enemy, _, _ in self.enemies: self.canvas.delete(enemy)
        self.enemies.clear()
        x0 = WINDOW_WIDTH//2 - BOSS_SIZE//2
        y0 = WINDOW_HEIGHT//2 - BOSS_SIZE//2
        x1 = WINDOW_WIDTH//2 + BOSS_SIZE//2
        y1 = WINDOW_HEIGHT//2 + BOSS_SIZE//2
        self.boss_warning = self.canvas.create_rectangle(x0, y0, x1, y1, fill=WARNING_COLOR)

    # --- Spawn solid boss ---
    def spawn_boss(self):
        if self.boss_warning:
            self.canvas.delete(self.boss_warning)
            self.boss_warning = None
        x0 = WINDOW_WIDTH//2 - BOSS_SIZE//2
        y0 = WINDOW_HEIGHT//2 - BOSS_SIZE//2
        x1 = WINDOW_WIDTH//2 + BOSS_SIZE//2
        y1 = WINDOW_HEIGHT//2 + BOSS_SIZE//2
        self.boss = self.canvas.create_rectangle(x0, y0, x1, y1, fill=BOSS_COLOR)
        self.boss_attack_running = True
        self.start_boss_attack()
        self.check_boss_collision()  # start collision detection for boss attacks

    # --- Boss attack cycle ---
    def start_boss_attack(self):
        if not self.boss_attack_running: return
        attack = random.choice([1,2,3,4])
        if attack==1: self.boss_attack_cross()
        elif attack==2: self.boss_attack_halfscreen()
        else: self.boss_attack_dummy()

    # --- Attack 1: rotating cross (edges) ---
    def boss_attack_cross(self):
        if not self.boss_attack_running: return
        if hasattr(self, "attack_squares"):
            for sq in self.attack_squares: self.canvas.delete(sq)
        self.attack_squares = []

        cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
        positions = [
            (cx, SMALL_ENEMY_SIZE//2),  # top
            (cx, WINDOW_HEIGHT - SMALL_ENEMY_SIZE//2),  # bottom
            (SMALL_ENEMY_SIZE//2, cy),  # left
            (WINDOW_WIDTH - SMALL_ENEMY_SIZE//2, cy)  # right
        ]
        for px, py in positions:
            sq = self.canvas.create_rectangle(
                px-SMALL_ENEMY_SIZE//2, py-SMALL_ENEMY_SIZE//2,
                px+SMALL_ENEMY_SIZE//2, py+SMALL_ENEMY_SIZE//2,
                fill=WARNING_COLOR
            )
            self.attack_squares.append(sq)

        self.add_timer(lambda: self.make_squares_solid(self.attack_squares), 1000)
        self.rotate_cross(positions, cx, cy, 0, True)

    def make_squares_solid(self, squares):
        for sq in squares: self.canvas.itemconfig(sq, fill=BOSS_COLOR)
        self.add_timer(lambda: [self.canvas.delete(sq) for sq in squares], 500)  # disappear after 0.5s

    def rotate_cross(self, positions, cx, cy, step, clockwise=True):
        if not self.boss_attack_running or step>36:
            self.add_timer(self.start_boss_attack, 500)
            return
        angle = math.radians(step*10*(1 if clockwise else -1))
        new_pos=[]
        for px, py in positions:
            dx, dy = px-cx, py-cy
            nx = dx*math.cos(angle)-dy*math.sin(angle)+cx
            ny = dx*math.sin(angle)+dy*math.cos(angle)+cy
            new_pos.append((nx, ny))
        for sq, (nx, ny) in zip(self.attack_squares, new_pos):
            self.canvas.coords(sq, nx-SMALL_ENEMY_SIZE//2, ny-SMALL_ENEMY_SIZE//2,
                                   nx+SMALL_ENEMY_SIZE//2, ny+SMALL_ENEMY_SIZE//2)
        self.add_timer(lambda: self.rotate_cross(positions, cx, cy, step+1, clockwise), BOSS_ATTACK_INTERVAL)

    # --- Attack 2: half-screen ---
    def boss_attack_halfscreen(self):
        if not self.boss_attack_running: return
        self.attack_squares=[]
        padding=30
        for i in range(padding, WINDOW_WIDTH//2, SMALL_ENEMY_SIZE*2):
            for j in range(padding, WINDOW_HEIGHT, SMALL_ENEMY_SIZE*2):
                if (WINDOW_WIDTH//2-BOSS_SIZE//2 < i < WINDOW_WIDTH//2+BOSS_SIZE//2) and \
                   (WINDOW_HEIGHT//2-BOSS_SIZE//2 < j < WINDOW_HEIGHT//2+BOSS_SIZE//2):
                    continue
                sq=self.canvas.create_rectangle(i,j,i+SMALL_ENEMY_SIZE,j+SMALL_ENEMY_SIZE, fill=WARNING_COLOR)
                self.attack_squares.append(sq)
        self.add_timer(lambda: self.make_squares_solid(self.attack_squares), 1000)
        self.add_timer(self.start_boss_attack, 3000)

    # --- Dummy attacks ---
    def boss_attack_dummy(self):
        if self.boss_attack_running:
            self.add_timer(self.start_boss_attack, 1000)

    # --- Boss attack collision with player ---
    def check_boss_collision(self):
        if not self.running or not self.boss_attack_running:
            return
        px1, py1, px2, py2 = self.canvas.coords(self.player)
        for sq in self.attack_squares:
            sx1, sy1, sx2, sy2 = self.canvas.coords(sq)
            if not (px2 < sx1 or px1 > sx2 or py2 < sy1 or py1 > sy2):
                self.game_over()
                return
        self.add_timer(self.check_boss_collision, 30)

    # --- Enemy spawning ---
    def spawn_enemies(self):
        if not self.running:
            return

        num_enemies = random.randint(self.enemy_min, self.enemy_max)
        for _ in range(num_enemies):
            for _ in range(20):
                x = random.randint(ENEMY_SIZE, WINDOW_WIDTH - ENEMY_SIZE)
                y = random.randint(ENEMY_SIZE + 30, WINDOW_HEIGHT - ENEMY_SIZE)
                dist = math.dist((x, y), (self.player_x, self.player_y))
                if dist > PLAYER_SIZE * 2:
                    break
            else:
                continue

            enemy = self.canvas.create_rectangle(
                x - ENEMY_SIZE // 2, y - ENEMY_SIZE // 2,
                x + ENEMY_SIZE // 2, y + ENEMY_SIZE // 2,
                fill="red"
            )
            dx = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
            dy = random.choice([-ENEMY_SPEED, ENEMY_SPEED])
            self.enemies.append((enemy, dx, dy))
            self.add_timer(lambda e=enemy: self.remove_enemy(e), ENEMY_LIFETIME)

        self.add_timer(self.spawn_enemies, ENEMY_SPAWN_INTERVAL)

    def remove_enemy(self, enemy):
        for e in list(self.enemies):
            if e[0] == enemy:
                self.canvas.delete(enemy)
                self.enemies.remove(e)
                break

    # --- Enemy movement with separation and reflection ---
    def move_enemies(self):
        if not self.running:
            return

        for i, (enemy, dx, dy) in enumerate(list(self.enemies)):
            ex1, ey1, ex2, ey2 = self.canvas.coords(enemy)
            cx = (ex1 + ex2) / 2
            cy = (ey1 + ey2) / 2

            # Wall bounce
            if ex1 <= 0 or ex2 >= WINDOW_WIDTH:
                dx = -dx
            if ey1 <= 0 or ey2 >= WINDOW_HEIGHT:
                dy = -dy

            # Enemy collisions
            for j, (other_enemy, odx, ody) in enumerate(self.enemies):
                if i == j:
                    continue
                ox1, oy1, ox2, oy2 = self.canvas.coords(other_enemy)
                ocx = (ox1 + ox2) / 2
                ocy = (oy1 + oy2) / 2

                dist = math.hypot(cx - ocx, cy - ocy)
                min_dist = ENEMY_SIZE
                if dist < min_dist and dist != 0:
                    # Normalized collision vector
                    nx = (cx - ocx) / dist
                    ny = (cy - ocy) / dist

                    # --- Separate overlapping enemies ---
                    overlap = min_dist - dist
                    cx += nx * (overlap / 2)
                    cy += ny * (overlap / 2)
                    ocx -= nx * (overlap / 2)
                    ocy -= ny * (overlap / 2)
                    self.canvas.coords(enemy, cx - ENEMY_SIZE / 2, cy - ENEMY_SIZE / 2,
                                                 cx + ENEMY_SIZE / 2, cy + ENEMY_SIZE / 2)
                    self.canvas.coords(other_enemy, ocx - ENEMY_SIZE / 2, ocy - ENEMY_SIZE / 2,
                                                      ocx + ENEMY_SIZE / 2, ocy + ENEMY_SIZE / 2)

                    # Reflect velocities
                    dvx = dx - odx
                    dvy = dy - ody
                    dot = dvx * nx + dvy * ny
                    dx -= dot * nx
                    dy -= dot * ny
                    odx += dot * nx
                    ody += dot * ny
                    self.enemies[j] = (other_enemy, odx, ody)

            # Move enemy
            self.canvas.move(enemy, dx, dy)
            self.enemies[i] = (enemy, dx, dy)

        self.add_timer(self.move_enemies, 50)

    # --- Difficulty scaling ---
    def level_up(self):
        if not self.running:
            return
        self.enemy_min += 3
        self.enemy_max += 7
        self.add_timer(self.level_up, LEVEL_UP_INTERVAL)

    # --- Collision detection ---
    def check_collision(self):
        if not self.running:
            return
        px1, py1, px2, py2 = self.canvas.coords(self.player)
        for enemy, _, _ in self.enemies:
            ex1, ey1, ex2, ey2 = self.canvas.coords(enemy)
            if not (px2 < ex1 or px1 > ex2 or py2 < ey1 or py1 > ey2):
                self.game_over()
                return
        self.add_timer(self.check_collision, 30)

    # --- Game over ---
    def game_over(self):
        self.running = False
        self.cancel_all_timers()
        elapsed = int(time.time() - self.start_time)
        score = elapsed * POINTS_PER_SECOND

        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30,
            text=f"GAME OVER\nScore: {score}",
            fill="white", font=("Arial", 32, "bold")
        )
        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40,
            text="Click to Retry",
            fill="gray", font=("Arial", 20)
        )


# --- Run Game ---
if __name__=="__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
