"""
Created on Wed Oct 29 14:41:36 2025
CourseWork for CSC-44102-2025-SEM1-A
@author: John Hamlyn 2201387701

Survival Game using Tkinter with Boss Stage 

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
SMALL_ENEMY_SIZE = 25
MAX_BOSS_ATTACKS = 4  # Boss disappears after 4 attacks

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
        self.boss_attack_count = 0

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
        self.boss_attack_count = 0

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

        # Boss every 30 seconds
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
        self.boss_attack_count = 0
        self.start_boss_attack()
        self.check_boss_collision()

    # --- Boss attack cycle ---
    def start_boss_attack(self):
        if not self.boss_attack_running: return
        if self.boss_attack_count >= MAX_BOSS_ATTACKS:
            self.end_boss()
            return
        self.boss_attack_count += 1

        attack = random.choice([1,2,3,4])
        if attack==1: self.boss_attack_cross()
        elif attack==2: self.boss_attack_halfscreen()
        elif attack==3: self.boss_attack_corners()
        elif attack==4: self.boss_attack_ring()

    # --- Attack 1: rotating cross ---
    def boss_attack_cross(self):
        if not self.boss_attack_running: return
        for sq in self.attack_squares: self.canvas.delete(sq)
        self.attack_squares = []

        cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
        step = SMALL_ENEMY_SIZE
        lines = []

        # Vertical and horizontal lines to edges
        for y in range(0, cy - BOSS_SIZE//2, step): lines.append((cx, y))
        for y in range(cy + BOSS_SIZE//2, WINDOW_HEIGHT, step): lines.append((cx, y))
        for x in range(0, cx - BOSS_SIZE//2, step): lines.append((x, cy))
        for x in range(cx + BOSS_SIZE//2, WINDOW_WIDTH, step): lines.append((x, cy))

        for px, py in lines:
            sq = self.canvas.create_rectangle(px-step//2, py-step//2, px+step//2, py+step//2, fill=WARNING_COLOR)
            self.attack_squares.append(sq)

        # Turn to solid red after 0.5s
        self.add_timer(lambda: [self.canvas.itemconfig(sq, fill=BOSS_COLOR) for sq in self.attack_squares], 500)

        # Rotate
        self.rotate_cross(0, True, step)

    def rotate_cross(self, step_count, clockwise, step):
        if not self.boss_attack_running: return
        if step_count > 72:
            if clockwise:
                self.rotate_cross(0, False, step)
            else:
                for sq in self.attack_squares: self.canvas.delete(sq)
                self.attack_squares = []
                self.add_timer(self.start_boss_attack, 500)
            return

        cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
        rotation_speed_factor = 0.04  # slower than before
        angle_per_step = math.radians(rotation_speed_factor * PLAYER_SPEED)
        angle = step_count * angle_per_step * (1 if clockwise else -1)

        new_pos = []
        for sq in self.attack_squares:
            coords = self.canvas.coords(sq)
            if not coords: continue
            px = (coords[0] + coords[2]) / 2
            py = (coords[1] + coords[3]) / 2
            dx, dy = px - cx, py - cy
            nx = dx*math.cos(angle) - dy*math.sin(angle) + cx
            ny = dx*math.sin(angle) + dy*math.cos(angle) + cy
            new_pos.append((nx, ny))

        for sq, (nx, ny) in zip(self.attack_squares, new_pos):
            self.canvas.coords(sq, nx-step/2, ny-step/2, nx+step/2, ny+step/2)

        self.add_timer(lambda: self.rotate_cross(step_count+1, clockwise, step), 150)

    # --- Attack 2: Half-screen ---
    def boss_attack_halfscreen(self):
        if not self.boss_attack_running: return
        self.attack_squares = []
        half_width = WINDOW_WIDTH // 2
        step = SMALL_ENEMY_SIZE
        padding = 30

        def spawn_half(x_start, x_end):
            squares = []
            for i in range(x_start, x_end, step*2):
                for j in range(padding, WINDOW_HEIGHT, step*2):
                    if (WINDOW_WIDTH//2-BOSS_SIZE//2 < i < WINDOW_WIDTH//2+BOSS_SIZE//2) and \
                       (WINDOW_HEIGHT//2-BOSS_SIZE//2 < j < WINDOW_HEIGHT//2+BOSS_SIZE//2):
                        continue
                    sq = self.canvas.create_rectangle(i, j, i+step, j+step, fill=WARNING_COLOR)
                    squares.append(sq)
            return squares

        left_squares = spawn_half(0, half_width)
        self.attack_squares = left_squares
        self.add_timer(lambda: [self.canvas.itemconfig(sq, fill=BOSS_COLOR) for sq in left_squares], 5200)

        def left_done():
            for sq in left_squares: self.canvas.delete(sq)
            right_squares = spawn_half(half_width, WINDOW_WIDTH)
            self.attack_squares = right_squares
            self.add_timer(lambda: [self.canvas.itemconfig(sq, fill=BOSS_COLOR) for sq in right_squares], 5200)
            def right_done():
                for sq in right_squares: self.canvas.delete(sq)
                self.attack_squares = []
                self.add_timer(self.start_boss_attack, 500)
            self.add_timer(right_done, 7200)
        self.add_timer(left_done, 5200)

    # --- Attack 3: Corners ---
    def boss_attack_corners(self):
        if not self.boss_attack_running: return
        self.attack_squares = []
        padding = 50
        positions = [
            (padding, padding),
            (WINDOW_WIDTH - padding, padding),
            (padding, WINDOW_HEIGHT - padding),
            (WINDOW_WIDTH - padding, WINDOW_HEIGHT - padding)
        ]
        for px, py in positions:
            sq = self.canvas.create_rectangle(
                px - SMALL_ENEMY_SIZE//2, py - SMALL_ENEMY_SIZE//2,
                px + SMALL_ENEMY_SIZE//2, py + SMALL_ENEMY_SIZE//2,
                fill=WARNING_COLOR
            )
            self.attack_squares.append(sq)

        self.add_timer(lambda: [self.canvas.itemconfig(sq, fill=BOSS_COLOR) for sq in self.attack_squares], 500)
        self.add_timer(lambda: [self.canvas.delete(sq) for sq in self.attack_squares], 2500)
        self.add_timer(self.start_boss_attack, 3000)

    # --- Attack 4: Ring ---
    def boss_attack_ring(self):
        if not self.boss_attack_running: return
        self.attack_squares = []
        cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
        radius = 150
        num_squares = 12
        for i in range(num_squares):
            angle = 2 * math.pi * i / num_squares
            px = cx + radius * math.cos(angle)
            py = cy + radius * math.sin(angle)
            sq = self.canvas.create_rectangle(
                px - SMALL_ENEMY_SIZE//2, py - SMALL_ENEMY_SIZE//2,
                px + SMALL_ENEMY_SIZE//2, py + SMALL_ENEMY_SIZE//2,
                fill=WARNING_COLOR
            )
            self.attack_squares.append(sq)

        self.add_timer(lambda: [self.canvas.itemconfig(sq, fill=BOSS_COLOR) for sq in self.attack_squares], 500)
        self.add_timer(lambda: [self.canvas.delete(sq) for sq in self.attack_squares], 2500)
        self.add_timer(self.start_boss_attack, 3000)

    # --- End boss ---
    def end_boss(self):
        for sq in self.attack_squares: self.canvas.delete(sq)
        if self.boss: self.canvas.delete(self.boss)
        self.attack_squares = []
        self.boss = None
        self.boss_attack_running = False
        self.boss_attack_count = 0

    # --- Boss collision ---
    def check_boss_collision(self):
        if not self.running:
            self.add_timer(self.check_boss_collision, 30)
            return
        px1, py1, px2, py2 = self.canvas.coords(self.player)
        self.attack_squares = [sq for sq in self.attack_squares if self.canvas.coords(sq)]
        for sq in self.attack_squares:
            coords = self.canvas.coords(sq)
            if not coords: continue
            sx1, sy1, sx2, sy2 = coords
            color = self.canvas.itemcget(sq, "fill")
            if color == BOSS_COLOR and not (px2 < sx1 or px1 > sx2 or py2 < sy1 or py1 > sy2):
                self.game_over()
                return
        self.add_timer(self.check_boss_collision, 30)

    # --- Enemy spawning ---
    def spawn_enemies(self):
        if not self.running or self.boss_attack_running:
            self.add_timer(self.spawn_enemies, ENEMY_SPAWN_INTERVAL)
            return
        num_enemies = random.randint(self.enemy_min, self.enemy_max)
        for _ in range(num_enemies):
            for _ in range(20):
                x = random.randint(ENEMY_SIZE, WINDOW_WIDTH - ENEMY_SIZE)
                y = random.randint(ENEMY_SIZE + 30, WINDOW_HEIGHT - ENEMY_SIZE)
                if math.dist((x, y), (self.player_x, self.player_y)) > PLAYER_SIZE * 2: break
            else: continue
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

    # --- Remove enemy ---
    def remove_enemy(self, enemy):
        for e in list(self.enemies):
            if e[0] == enemy:
                self.canvas.delete(enemy)
                self.enemies.remove(e)
                break

    # --- Enemy movement ---
    def move_enemies(self):
        if not self.running: return
        for i, (enemy, dx, dy) in enumerate(list(self.enemies)):
            ex1, ey1, ex2, ey2 = self.canvas.coords(enemy)
            cx = (ex1 + ex2) / 2
            cy = (ey1 + ey2) / 2
            if ex1 <= 0 or ex2 >= WINDOW_WIDTH: dx = -dx
            if ey1 <= 0 or ey2 >= WINDOW_HEIGHT: dy = -dy
            for j, (other_enemy, odx, ody) in enumerate(self.enemies):
                if i == j: continue
                ox1, oy1, ox2, oy2 = self.canvas.coords(other_enemy)
                ocx = (ox1 + ox2)/2; ocy = (oy1 + oy2)/2
                dist = math.hypot(cx - ocx, cy - ocy)
                if dist < ENEMY_SIZE and dist != 0:
                    nx = (cx - ocx)/dist; ny = (cy - ocy)/dist
                    overlap = ENEMY_SIZE - dist
                    cx += nx*overlap/2; cy += ny*overlap/2
                    ocx -= nx*overlap/2; ocy -= ny*overlap/2
                    self.canvas.coords(enemy, cx-ENEMY_SIZE/2, cy-ENEMY_SIZE/2, cx+ENEMY_SIZE/2, cy+ENEMY_SIZE/2)
                    self.canvas.coords(other_enemy, ocx-ENEMY_SIZE/2, ocy-ENEMY_SIZE/2, ocx+ENEMY_SIZE/2, ocy+ENEMY_SIZE/2)
                    dvx = dx - odx; dvy = dy - ody
                    dot = dvx*nx + dvy*ny
                    dx -= dot*nx; dy -= dot*ny
                    odx += dot*nx; ody += dot*ny
                    self.enemies[j] = (other_enemy, odx, ody)
            self.canvas.move(enemy, dx, dy)
            self.enemies[i] = (enemy, dx, dy)
        self.add_timer(self.move_enemies, 50)

    # --- Difficulty scaling ---
    def level_up(self):
        if not self.running: return
        self.enemy_min += 3; self.enemy_max += 7
        self.add_timer(self.level_up, LEVEL_UP_INTERVAL)

    # --- Collision detection ---
    def check_collision(self):
        if not self.running: return
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

if __name__=="__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
