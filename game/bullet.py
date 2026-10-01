import pygame

class Bullet:
    def __init__(self, x, y, width=4, height=12, speed=8, direction=-1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.direction = direction  # -1 = moving up (player bullet), 1 = moving down (enemy bullet)
        self.prev_y = y

    def move(self):
        self.prev_y = self.y
        self.y += self.speed * self.direction

    def off_screen(self, screen_height):
        return self.y < 0 or self.y > screen_height

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def swept_rect(self):
        """Rect covering everything the bullet passed through this frame,
        so a fast bullet can't skip over a target between two frames."""
        top = min(self.prev_y, self.y)
        height = abs(self.y - self.prev_y) + self.height
        return pygame.Rect(self.x, top, self.width, height)
