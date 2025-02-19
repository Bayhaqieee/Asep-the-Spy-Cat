import pygame
import sys
import random
import time
from queue import PriorityQueue

WIDTH, HEIGHT = 20, 20
CELL_SIZE = 30
WALL, EMPTY, PLAYER, PAWN, HUNTER, FINISH = '#', '.', 'P', 'pawn', 'hunter', 'F'
MOVE_KEYS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_w: (0, -1),
    pygame.K_s: (0, 1),
    pygame.K_a: (-1, 0),
    pygame.K_d: (1, 0),
}
Enemy_movement = 1500
Noise_decrease = 500

class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = self.generate_maze()
        self.player_pos = (1, 1)
        self.grid[1][1] = PLAYER
        self.finish_pos = (height-2, width-2)
        self.grid[self.finish_pos[0]][self.finish_pos[1]] = FINISH
        self.enemies = self.summon_enemies()
        self.noise_level = 0
        self.noise_decay_start_time = 0
        self.last_enemy_move_time = pygame.time.get_ticks()
        self.last_player_move_time = pygame.time.get_ticks()

    def generate_maze(self):
        def carve_passages_from(cx, cy, grid):
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            for direction in directions:
                nx, ny = cx + direction[0] * 2, cy + direction[1] * 2
                if 1 <= nx < self.width and 1 <= ny < self.height and grid[ny][nx] == WALL:
                    grid[ny - direction[1]][nx - direction[0]] = EMPTY
                    grid[ny][nx] = EMPTY
                    carve_passages_from(nx, ny, grid)

        grid = [[WALL for _ in range(self.width)] for _ in range(self.height)]
        grid[1][1] = EMPTY
        carve_passages_from(1, 1, grid)

        for _ in range(int(self.width * self.height * 0.1)):
            x, y = random.randint(1, self.width-2), random.randint(1, self.height-2)
            grid[y][x] = EMPTY

        return grid

    def summon_enemies(self):
        enemies = []
        num_pawns = 3
        num_hunters = 1

        for _ in range(num_pawns):
            while True:
                path_length = random.randint(3, 6)
                path = self.generate_random_path(path_length)
                if path and not self.is_in_front_of_player(path[0]):
                    enemies.append({'type': PAWN, 'path': path, 'current_step': 0})
                    break
                
        for _ in range(num_hunters):
            while True:
                start_pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
                if start_pos != self.player_pos and start_pos != self.finish_pos and self.grid[start_pos[1]][start_pos[0]] == EMPTY:
                    enemies.append({'type': HUNTER, 'pos': start_pos, 'detection_range': 1, 'chasing': False, 'chase_path': [], 'active': False})
                    self.grid[start_pos[1]][start_pos[0]] = HUNTER
                    break

        return enemies

    def is_in_front_of_player(self, position):
        px, py = self.player_pos
        return abs(px - position[0]) + abs(py - position[1]) <= 1

    def generate_random_path(self, length):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        start_pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
        while start_pos == self.player_pos or start_pos == self.finish_pos or self.grid[start_pos[1]][start_pos[0]] == WALL:
            start_pos = (random.randint(1, self.width-2), random.randint(1, self.height-2))
        path = [start_pos]

        for _ in range(length - 1):
            last_x, last_y = path[-1]
            valid_directions = [direction for direction in directions
                                if 0 < last_x + direction[0] < self.width-1
                                and 0 < last_y + direction[1] < self.height-1
                                and self.grid[last_y + direction[1]][last_x + direction[0]] != WALL]

            if not valid_directions:
                break

            direction = random.choice(valid_directions)
            new_x, new_y = last_x + direction[0], last_y + direction[1]

            if (new_x, new_y) != self.player_pos and (new_x, new_y) != self.finish_pos:
                path.append((new_x, new_y))

        if len(path) < length:
            return None 
        return path
    
    def move_player(self, dx, dy):
        new_x, new_y = self.player_pos[0] + dx, self.player_pos[1] + dy
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            if self.grid[new_y][new_x] == EMPTY or self.grid[new_y][new_x] == FINISH:
                self.grid[self.player_pos[1]][self.player_pos[0]] = EMPTY
                self.player_pos = (new_x, new_y)
                self.grid[new_y][new_x] = PLAYER
                self.noise_level += 1
                self.noise_decay_start_time = pygame.time.get_ticks()
                self.last_player_move_time = pygame.time.get_ticks()
                if (new_x, new_y) == self.finish_pos:
                    print("Congratulations! You reached the finish line.")
                    pygame.quit()
                    sys.exit()
            elif self.grid[new_y][new_x] == PAWN or self.grid[new_y][new_x] == HUNTER:
                print("Game over! You were detected by an enemy.")
                pygame.quit()
                sys.exit()

    def move_enemies(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_enemy_move_time >= Enemy_movement:
            self.last_enemy_move_time = current_time
            for enemy in self.enemies:
                if enemy['type'] == PAWN:
                    self.move_pawn(enemy)
                elif enemy['type'] == HUNTER and enemy['chasing']:
                    self.move_hunter(enemy)

    def move_pawn(self, pawn):
        path = pawn['path']
        current_step = pawn['current_step']
        next_step = (current_step + 1) % len(path)
        current_pos = path[current_step]
        next_pos = path[next_step]

        self.grid[current_pos[1]][current_pos[0]] = EMPTY
        self.grid[next_pos[1]][next_pos[0]] = PAWN

        pawn['current_step'] = next_step

        # Check for noise detection
        if self.noise_level > 0:
            player_x, player_y = self.player_pos
            enemy_x, enemy_y = next_pos
            if abs(player_x - enemy_x) + abs(player_y - enemy_y) <= 3:
                for enemy in self.enemies:
                    if enemy['type'] == HUNTER:
                        enemy['chasing'] = True
                        enemy['chase_path'] = self.a_star_pathfinding((enemy['pos'][1], enemy['pos'][0]), self.player_pos)

    def move_hunter(self, hunter):
        current_pos = hunter['pos']

        if hunter['chasing']:
            if hunter['chase_path']:
                next_pos = hunter['chase_path'].pop(0)
                if self.is_position_valid((next_pos[1], next_pos[0])):
                    next_x, next_y = next_pos
                    if self.grid[next_y][next_x] == PLAYER:
                        print("Game over! You were detected by a hunter.")
                        pygame.quit()
                        sys.exit()
                    self.grid[current_pos[1]][current_pos[0]] = EMPTY
                    self.grid[next_y][next_x] = HUNTER
                    hunter['pos'] = (next_x, next_y)
                else:
                    hunter['chasing'] = False
                    
    def a_star_pathfinding(self, start, goal):
        def heuristic(pos1, pos2):
            x1, y1 = pos1
            x2, y2 = pos2
            return abs(x1 - x2) + abs(y1 - y2)

        start = (start[1], start[0])
        goal = (goal[1], goal[0])

        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}

        while not open_set.empty():
            current = open_set.get()[1]

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return [(y, x) for x, y in path]

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if self.is_position_valid(neighbor):
                    tentative_g_score = g_score[current] + 1
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                        open_set.put((f_score[neighbor], neighbor))

        return []

    def is_position_valid(self, pos):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] != WALL
    
    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if self.grid[y][x] == PLAYER:
                    pygame.draw.rect(screen, (0, 255, 0), rect)
                elif self.grid[y][x] == WALL:
                    pygame.draw.rect(screen, (139, 69, 19), rect)
                elif self.grid[y][x] == EMPTY:
                    pygame.draw.rect(screen, (200, 200, 200), rect)
                elif self.grid[y][x] == PAWN:
                    pygame.draw.rect(screen, (255, 165, 0), rect)
                elif self.grid[y][x] == HUNTER:
                    pygame.draw.rect(screen, (255, 0, 0), rect)
                elif self.grid[y][x] == FINISH:
                    pygame.draw.rect(screen, (0, 0, 255), rect)
                else:
                    pygame.draw.rect(screen, (200, 200, 200), rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        self.highlight_movement(screen)

        current_time = pygame.time.get_ticks()
        if current_time - self.noise_decay_start_time <= 2000:
            font = pygame.font.Font(None, 36)
            noise_text = font.render(f"Noise Level: {self.noise_level}", True, (0, 0, 0))
            screen.blit(noise_text, (10, 10))
    
    def highlight_movement(self, screen):
        px, py = self.player_pos
        noise_radius = self.noise_level

        def can_propagate(nx, ny):
            return 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] != WALL

        visited = set()
        queue = [(px, py, 0)]

        while queue:
            cx, cy, dist = queue.pop(0)
            if (cx, cy) in visited or dist > noise_radius:
                continue

            visited.add((cx, cy))

            rect = pygame.Rect(cx * CELL_SIZE, cy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if can_propagate(nx, ny):
                    queue.append((nx, ny, dist + 1))

    def update_noise(self):
        current_time = pygame.time.get_ticks()
        if self.noise_level > 0 and current_time - self.noise_decay_start_time >= Noise_decrease:
            self.noise_level -= 1
            self.noise_decay_start_time = current_time

def main_menu(screen):
    font = pygame.font.Font(None, 74)
    title_text = font.render("Asep the Spy Cat", True, (0, 0, 0))
    start_button = pygame.Rect(WIDTH * CELL_SIZE // 2 - 100, HEIGHT * CELL_SIZE // 2, 200, 50)
    start_text = pygame.font.Font(None, 36).render("Start", True, (0, 0, 0))

    while True:
        screen.fill((255, 255, 255))
        screen.blit(title_text, (WIDTH * CELL_SIZE // 2 - title_text.get_width() // 2, HEIGHT * CELL_SIZE // 3))
        pygame.draw.rect(screen, (0, 0, 0), start_button)
        screen.blit(start_text, (start_button.x + (start_button.width - start_text.get_width()) // 2, start_button.y + (start_button.height - start_text.get_height()) // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button.collidepoint(event.pos):
                    return

        pygame.display.flip()

def loading_screen(screen):
    font = pygame.font.Font(None, 74)
    loading_text = font.render("Loading...", True, (0, 0, 0))
    screen.fill((255, 255, 255))
    screen.blit(loading_text, (WIDTH * CELL_SIZE // 2 - loading_text.get_width() // 2, HEIGHT * CELL_SIZE // 2))
    pygame.display.flip()

    time.sleep(2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE))
    pygame.display.set_caption("Asep the Spy Cat")
    clock = pygame.time.Clock()

    main_menu(screen)
    loading_screen(screen)
    
    game_map = GameMap(WIDTH, HEIGHT)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in MOVE_KEYS:
                    dx, dy = MOVE_KEYS[event.key]
                    game_map.move_player(dx, dy)
        
        game_map.move_enemies()
        game_map.update_noise()

        screen.fill((255, 255, 255))
        game_map.render(screen)
        pygame.display.flip()
        clock.tick(180)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()