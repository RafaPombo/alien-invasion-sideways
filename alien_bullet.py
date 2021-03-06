import pygame
from pygame.sprite import Sprite


class AlienBullet(Sprite):
    """A class to manage bullets fired from the aliens."""

    def __init__(self, ai_game, alien):
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = self.settings.alien_bullet_color

        self.rect = pygame.Rect(0, 0, self.settings.alien_bullet_width, self.settings.alien_bullet_height)

        self.rect.midleft = alien.rect.midleft

        self.x = float(self.rect.x)

    def update(self):
        self.x -= self.settings.alien_bullet_speed
        self.rect.x = self.x

    def draw_bullet(self):
        pygame.draw.rect(self.screen, self.color, self.rect)