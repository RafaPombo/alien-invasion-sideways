import sys
import pygame
from time import sleep
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien_bullet import AlienBullet
from alien import Alien
from random import randint


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics and create a scoreboard.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()

        self._create_fleet()

        # Make the Play button.
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()

            if self.stats.game_active:
                for alien in self.aliens:
                    self._fire_alien_bullet(alien)
                self._update_images()

            self._update_screen()

    def _update_images(self):
        """Update game images"""
        self.ship.update()
        self._update_bullets()
        self._update_aliens()
        self._update_alien_bullets()

    def _check_events(self):
        """Respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()

            # Reset the game statistics.
            self.stats.reset_stats()

            self._start_game()

    def _start_game(self):
        """Sets up aspects needed for the game to start."""
        # Set the game as active.
        self.stats.game_active = True

        # Set up game images.
        self.sb.prep_images()

        # Get rid of any remaining aliens and bullets.
        self.aliens.empty()
        self.bullets.empty()
        self.alien_bullets.empty()

        # Create a new fleet and center the ship.
        self._create_fleet()
        self.ship.center_ship()

        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        elif event.key == pygame.K_q:
            # Save highscore to a text file and close the game.
            with open('highscore.txt', 'w') as f:
                f.write(str(self.stats.high_score))
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _fire_alien_bullet(self, alien):
        """Create a new alien bullet and add it to the alien_bullets group."""
        probability = self.settings.alien_bullet_probability
        randnum = randint(0, 100000)
        if randnum <= probability:
            new_bullet = AlienBullet(self, alien)
            self.alien_bullets.add(new_bullet)

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_DOWN:
            self.ship.moving_down = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _start_new_level(self):
        """Starts a new level."""
        # Destroy existing bullets and create new fleet.
        self.bullets.empty()
        self._create_fleet()
        self.settings.increase_speed()

        # Increase level.
        self.stats.level += 1
        self.sb.prep_level()

    def _update_aliens(self):
        """
        Check if the fleet is at an edge,
        then update the positions of all aliens in the fleet.
        """
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        self._check_aliens_leftside()

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.left >= self.sb.background_rect.left:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _update_alien_bullets(self):
        """Update alien bullet positions and get rid of old ones."""
        # Update bullet positions.
        self.alien_bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.alien_bullets.copy():
            if bullet.rect.top >= self.screen.get_height():
                self.alien_bullets.remove(bullet)

        self._check_bullet_ship_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for alien in collisions.values():
                self.stats.score += self.settings.alien_points * len(alien)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            self._start_new_level()

    def _check_bullet_ship_collisions(self):
        """Respond to bullet-ship collisions."""
        # Restart level and decrease ship amount by 1.
        collisions = pygame.sprite.spritecollide(self.ship, self.alien_bullets, False, False)

        if collisions:
            self._ship_hit()

    def _reset_level(self):
        """Resets the current level."""
        # Decrement ships_left and update scoreboard.
        self.stats.ships_left -= 1
        self.sb.prep_ships()

        # Get rid of any remaining aliens and bullets.
        self.aliens.empty()
        self.bullets.empty()
        self.alien_bullets.empty()

        # Create a new fleet and center the ship.
        self._create_fleet()
        self.ship.center_ship()

        # Pause.
        sleep(0.5)

    def _create_fleet(self):
        """Create the fleet of aliens."""

        number_aliens_y, number_columns = self._alien_setup()

        # Create the full fleet of aliens.
        for column_number in range(number_columns):
            for alien_number in range(number_aliens_y):
                self._create_alien(alien_number, column_number)

    def _alien_setup(self):
        """
        Determines the number of columns of aliens
        and the number of aliens in each column.
        """
        # Create an alien and find the number of aliens in a column.
        # Spacing between each alien is equal to one alien height.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_y = self.settings.screen_height - (2 * alien_height)
        number_aliens_y = available_space_y // (2 * alien_height)

        # Determine the number of columns of aliens that fit on the screen.
        ship_width = self.ship.rect.width
        available_space_x = (self.settings.screen_width - (10 * alien_width) - ship_width)
        number_columns = available_space_x // (2 * alien_width)

        return number_aliens_y, number_columns

    def _create_alien(self, alien_number, row_number):
        """Create an alien and place it in the row."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.y = alien_height + 2 * alien_height * alien_number
        alien.rect.y = alien.y
        alien.rect.x = 400 + alien.rect.width + 2 * alien.rect.width * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Move the entire fleet to the left and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.x -= self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            self._reset_level()
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_leftside(self):
        """Check if any aliens have reached the left side of the screen."""
        for alien in self.aliens.sprites():
            if alien.rect.left <= 0:
                # Treat this the same as if the ship got hit.
                self._ship_hit()
                break

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()

        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        for bullet in self.alien_bullets.sprites():
            bullet.draw_bullet()

        self.aliens.draw(self.screen)

        # Draw the score information.
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()