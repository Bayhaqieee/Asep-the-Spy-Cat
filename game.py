import pygame
import sys
import random

WIDTH, HEIGHT = 10, 10
CELL_SIZE = 40
WALL, EMPTY, PLAYER, ENEMY, FINISH = '#', '.', 'P', 'E', 'F'
MOVE_KEYS = {
    pygame.K_UP: (-1, 0),
    pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1),
    pygame.K_RIGHT: (0, 1),
    pygame.K_w: (-1, 0),
    pygame.K_s: (1, 0),
    pygame.K_a: (0, -1),
    pygame.K_d: (0, 1),
}

class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[EMPTY for _ in range(width)] for _ in range(height)]
        self.player_pos = (1, 1)
        self.grid[1][1] = PLAYER
        self.grid[height-2][width-2] = FINISH
        self.enemies = self.spawn_enemies()
        self.noise_level = 0
        self.noise_cooldown = 0

    def spawn_enemies(self):
        enemies = []
        num_enemies = 3
        for _ in range(num_enemies):
            path_length = random.randint(3, 6)
            path = self.generate_random_path(path_length)
            if path:
                enemies.append({'path': path, 'current_step': 0, 'detection_range': 3})
        return enemies

    def generate_random_path(self, length):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        start_pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
        path = [start_pos]

        for _ in range(length - 1):
            last_x, last_y = path[-1]
            direction = random.choice(directions)
            new_x, new_y = last_x + direction[0], last_y + direction[1]
            if 0 < new_x < self.width-1 and 0 < new_y < self.height-1 and self.grid[new_x][new_y] == EMPTY:
                path.append((new_x, new_y))
            else:
                break

        if len(path) < length:
            return None
        return path
    
    def move_player(self, dx, dy):
        new_x, new_y = self.player_pos[0] + dx, self.player_pos[1] + dy
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            if self.grid[new_x][new_y] == EMPTY or self.grid[new_x][new_y] == FINISH:
                self.grid[self.player_pos[0]][self.player_pos[1]] = EMPTY
                self.player_pos = (new_x, new_y)
                self.grid[new_x][new_y] = PLAYER
                self.noise_level += 1
                self.noise_cooldown = 0
            elif self.grid[new_x][new_y] == ENEMY:
                print("Game over! You were detected by an enemy.")
                pygame.quit()
                sys.exit()

    def move_enemies(self):
        for enemy in self.enemies:
            path = enemy['path']
            current_step = enemy['current_step']
            next_step = (current_step + 1) % len(path)
            current_pos = path[current_step]
            next_pos = path[next_step]

            if self.grid[current_pos[0]][current_pos[1]] == ENEMY:
                self.grid[current_pos[0]][current_pos[1]] = EMPTY
            self.grid[next_pos[0]][next_pos[1]] = ENEMY

            enemy['current_step'] = next_step

            # Check noise detection
            if self.noise_level > 0:
                player_x, player_y = self.player_pos
                if abs(player_x - next_pos[0]) + abs(player_y - next_pos[1]) <= enemy['detection_range']:
                    print("Game over! You were detected by an enemy.")
                    pygame.quit()
                    sys.exit()
                    
    def render(self, screen):
        pass

    def update_noise(self):
        pass

def main():
    pass

if __name__ == "__main__":
    main()