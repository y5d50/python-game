"""
Created on Wed Oct 29 14:41:36 2025
CourseWork for CSC-44102-2025-SEM1-A
@author: John Hamlyn 2201387701

Survival Game using Tkinter

Acknowledgment:
This project has benefited from the use of AI assistance (OpenAI's ChatGPT)
for code optimization, debugging, and providing guidance on structuring 
game logic and event handling.
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
ENEMY_SPAWN_INTERVAL = 10000       # every 10 seconds
ENEMY_LIFETIME = 9500              # 9.5 seconds
LEVEL_UP_INTERVAL = 20000          # every 20 seconds
POINTS_PER_SECOND = 10


class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Survival Game")
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="black")
        self.canvas.pack()

        self.running = False
        self.active_timers = []

        # Initial menu text
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
            return  # Prevent restarting mid-game

        self.cancel_all_timers()
        self.canvas.delete("all")

        # Player setup
        self.player_x = WINDOW_WIDTH // 2
        self.player_y = WINDOW_HEIGHT // 2
        self.player = self.canvas.create_rectangle(
            self.player_x - PLAYER_SIZE // 2, self.player_y - PLAYER_SIZE // 2,
            self.player_x + PLAYER_SIZE // 2, self.player_y + PLAYER_SIZE // 2,
            fill="cyan"
        )

        self.start_time = time.time()
        self.enemies = []
        self.enemy_min = 3
        self.enemy_max = 6
        self.keys_pressed = set()
        self.running = True

        # Timer display
        self.timer_text = self.canvas.create_text(
            10, 10, anchor="nw", fill="white", font=("Arial", 16), text="Time: 0"
        )

        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

        # Start game loops
        self.add_timer(self.update_timer, 1000)
        self.update_player_position()
        self.spawn_enemies()
        self.move_enemies()
        self.add_timer(self.level_up, LEVEL_UP_INTERVAL)
        self.check_collision()

    # --- Player controls ---
    def key_press(self, event):
        if not self.running:
            return
        self.keys_pressed.add(event.keysym.lower())

    def key_release(self, event):
        if event.keysym.lower() in self.keys_pressed:
            self.keys_pressed.remove(event.keysym.lower())

    def update_player_position(self):
        if not self.running:
            return

        if 'w' in self.keys_pressed:
            self.player_y -= PLAYER_SPEED
        if 's' in self.keys_pressed:
            self.player_y += PLAYER_SPEED
        if 'a' in self.keys_pressed:
            self.player_x -= PLAYER_SPEED
        if 'd' in self.keys_pressed:
            self.player_x += PLAYER_SPEED

        self.player_x = max(PLAYER_SIZE // 2, min(WINDOW_WIDTH - PLAYER_SIZE // 2, self.player_x))
        self.player_y = max(PLAYER_SIZE // 2, min(WINDOW_HEIGHT - PLAYER_SIZE // 2, self.player_y))

        self.canvas.coords(
            self.player,
            self.player_x - PLAYER_SIZE // 2, self.player_y - PLAYER_SIZE // 2,
            self.player_x + PLAYER_SIZE // 2, self.player_y + PLAYER_SIZE // 2
        )

        self.add_timer(self.update_player_position, 20)

    # --- Game timer ---
    def update_timer(self):
        if not self.running:
            return
        elapsed = int(time.time() - self.start_time)
        self.canvas.itemconfig(self.timer_text, text=f"Time: {elapsed}")
        self.add_timer(self.update_timer, 1000)

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


# --- Run game ---
if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
