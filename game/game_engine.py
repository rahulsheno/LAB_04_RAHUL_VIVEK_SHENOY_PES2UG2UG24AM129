import pygame
import random
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)

# Difficulty presets: enemy march speed and per-enemy chance to fire each frame.
# "Medium" matches the original game's enemy speed.
DIFFICULTIES = {
    "Easy":   {"key": pygame.K_1, "speed": 1.0, "fire_chance": 0.0003},
    "Medium": {"key": pygame.K_2, "speed": 1.5, "fire_chance": 0.0006},
    "Hard":   {"key": pygame.K_3, "speed": 2.5, "fire_chance": 0.0012},
}
DEFAULT_DIFFICULTY = "Medium"


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 30)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 22)
        self.quit_requested = False

        self.reset(DEFAULT_DIFFICULTY)

    def reset(self, difficulty):
        """Start a fresh round at the given difficulty (a key of DIFFICULTIES)."""
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty

        self.player = Player(self.width // 2 - 20, self.height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(self.width, speed=settings["speed"])

        self.player_bullets = []
        self.enemy_bullets = []
        self._shoot_cooldown = 0
        self.enemy_fire_chance = settings["fire_chance"]

        self.score = 0
        self.game_over = False
        self.won = False

    def handle_event(self, event):
        if self.game_over:
            self._handle_game_over_event(event)
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self._shoot_cooldown <= 0:
                bullet_x = self.player.center_x() - 2
                self.player_bullets.append(Bullet(bullet_x, self.player.y, direction=-1))
                self._shoot_cooldown = 15

    def _handle_game_over_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.quit_requested = True
            return
        for name, settings in DIFFICULTIES.items():
            if event.key == settings["key"]:
                self.reset(name)
                return

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-self.player.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(self.player.speed, self.width)

    def update(self):
        if self.game_over:
            return

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        self.enemy_grid.move()

        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < self.enemy_fire_chance:
                bullet_x = enemy.x + enemy.width // 2
                self.enemy_bullets.append(Bullet(bullet_x, enemy.y + enemy.height, direction=1))

        for bullet in self.player_bullets:
            bullet.move()
        for bullet in self.enemy_bullets:
            bullet.move()

        self.player_bullets = [b for b in self.player_bullets if not b.off_screen(self.height)]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.off_screen(self.height)]

        self._resolve_player_bullet_hits()

        for bullet in self.enemy_bullets:
            if bullet.swept_rect().colliderect(self.player.rect()):
                self.game_over = True
                break

        if self.enemy_grid.reached_bottom(self.player.y):
            self.game_over = True

        if not self.enemy_grid.alive_enemies():
            self.game_over = True
            self.won = True

    def _resolve_player_bullet_hits(self):
        """Each bullet destroys at most one enemy, each enemy dies at most once.

        Surviving bullets are collected into a new list instead of calling
        list.remove() while iterating, which used to skip the bullet after
        every removed one.
        """
        targets = self.enemy_grid.alive_enemies()
        surviving = []
        for bullet in self.player_bullets:
            bullet_rect = bullet.swept_rect()
            hit = None
            for enemy in targets:
                if enemy.alive and bullet_rect.colliderect(enemy.rect()):
                    hit = enemy
                    break
            if hit is None:
                surviving.append(bullet)
            else:
                hit.alive = False
                self.score += 1
        self.player_bullets = surviving

    def render(self, screen):
        pygame.draw.rect(screen, GREEN, self.player.rect())

        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(screen, WHITE, enemy.rect())

        for bullet in self.player_bullets:
            pygame.draw.rect(screen, WHITE, bullet.rect())
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            self._render_game_over(screen)

    def _draw_centered(self, screen, font, text, color, y):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))

    def _render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title, color = ("YOU WIN!", GREEN) if self.won else ("GAME OVER", RED)
        self._draw_centered(screen, self.title_font, title, color, self.height // 2 - 70)
        self._draw_centered(screen, self.font, f"Final Score: {self.score}", WHITE, self.height // 2 + 5)
        self._draw_centered(screen, self.small_font, "Play again - choose difficulty:", WHITE, self.height // 2 + 65)
        for i, (name, settings) in enumerate(DIFFICULTIES.items()):
            label = f"[{i + 1}] {name}" + ("  (last played)" if name == self.difficulty else "")
            self._draw_centered(screen, self.small_font, label, GREEN, self.height // 2 + 100 + i * 30)
        self._draw_centered(screen, self.small_font, "[Q] or [ESC] to exit", RED, self.height // 2 + 100 + len(DIFFICULTIES) * 30 + 10)
