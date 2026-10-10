import pygame
import random
import math
import sys
import serial

from start_screen import StartScreen
from pace_manager import PaceManager

# --------------------------------------------------
# Initialize Pygame
# --------------------------------------------------
pygame.init()

# Game constants
WIDTH, HEIGHT = 800, 600
FPS = 60

MAX_LIVES = 3
INVULNERABILITY_MS = 2000
LIFE_FLASH_MS = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)

# Asteroid sizes
LARGE_ASTROID = 40
MEDIUM_ASTROID = 20
SMALL_ASTROID = 10

# Serial connection (optional)
try:
    arduino = serial.Serial(
        "/dev/cu.usbmodem13201",
        9600,
        timeout=0,
    )
except (serial.SerialException, OSError):
    print("Microcontroller not found. Using keyboard controls.")
    arduino = None

# Display setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Asteroids Shooter")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24, bold=True)
button_font = pygame.font.SysFont("Arial", 20, bold=True)

start_screen = StartScreen(WIDTH, HEIGHT)


# --------------------------------------------------
# Shared ship geometry
# --------------------------------------------------
def get_ship_points(x, y, angle, radius):
    """Return the three vertices of a triangular ship."""

    tip_x = x + math.cos(math.radians(angle)) * radius * 2
    tip_y = y - math.sin(math.radians(angle)) * radius * 2

    left_x = x + math.cos(
        math.radians(angle + 130)
    ) * radius
    left_y = y - math.sin(
        math.radians(angle + 130)
    ) * radius

    right_x = x + math.cos(
        math.radians(angle - 130)
    ) * radius
    right_y = y - math.sin(
        math.radians(angle - 130)
    ) * radius

    return [
        (int(tip_x), int(tip_y)),
        (int(left_x), int(left_y)),
        (int(right_x), int(right_y)),
    ]


def draw_lives(surface, lives, last_lost_time):
    """Draw three ship icons to represent the player's lives."""

    now = pygame.time.get_ticks()

    start_x = WIDTH - 105
    y = 28
    spacing = 35
    icon_radius = 7

    for index in range(MAX_LIVES):
        x = start_x + index * spacing

        points = get_ship_points(
            x, y, 90, icon_radius
        )

        if index < lives:
            pygame.draw.polygon(
                surface, WHITE, points, 2
            )

        elif (
            index == lives
            and last_lost_time is not None
            and now - last_lost_time < LIFE_FLASH_MS
        ):
            pygame.draw.polygon(
                surface, RED, points
            )
            pygame.draw.polygon(
                surface, RED, points, 2
            )

        else:
            pygame.draw.polygon(
                surface, GRAY, points, 2
            )


# --------------------------------------------------
# Player
# --------------------------------------------------
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 90
        self.speed = 0
        self.radius = 15

        self.invulnerable_until = 0

    def is_invulnerable(self):
        return (
            pygame.time.get_ticks()
            < self.invulnerable_until
        )

    def draw(self, surface):
        if self.is_invulnerable():
            blink_interval = 120
            if (
                pygame.time.get_ticks() // blink_interval
            ) % 2 == 0:
                return

        points = get_ship_points(
            self.x,
            self.y,
            self.angle,
            self.radius,
        )

        pygame.draw.polygon(
            surface, WHITE, points, 2
        )

    def update(self):
        if arduino:
            while arduino.in_waiting > 0:
                try:
                    raw_data = arduino.readline().decode(
                        "utf-8"
                    ).strip()

                    if "," in raw_data:
                        x_str, y_str = raw_data.split(",")
                        x_val = int(x_str)
                        y_val = int(y_str)

                        if x_val < -5:
                            self.angle += 5
                        elif x_val > 5:
                            self.angle -= 5

                        if y_val > 5:
                            self.speed = 5
                        else:
                            self.speed = 0

                except (UnicodeDecodeError, ValueError):
                    pass

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.angle += 5

        if keys[pygame.K_RIGHT]:
            self.angle -= 5

        if keys[pygame.K_UP]:
            self.speed = 5
        elif not arduino:
            self.speed = 0

        self.x += math.cos(
            math.radians(self.angle)
        ) * self.speed

        self.y -= math.sin(
            math.radians(self.angle)
        ) * self.speed

        self.x %= WIDTH
        self.y %= HEIGHT


# --------------------------------------------------
# Bullet
# --------------------------------------------------
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 3

    def update(self):
        self.x += math.cos(
            math.radians(self.angle)
        ) * self.speed

        self.y -= math.sin(
            math.radians(self.angle)
        ) * self.speed

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            RED,
            (int(self.x), int(self.y)),
            self.radius,
        )


# --------------------------------------------------
# Asteroid
# --------------------------------------------------
class Asteroid:
    def __init__(self, x, y, size, speed_range=(1.0, 3.0)):
        self.x = x
        self.y = y
        self.size = size

        if size == 3:
            self.radius = LARGE_ASTROID
        elif size == 2:
            self.radius = MEDIUM_ASTROID
        else:
            self.radius = SMALL_ASTROID

        self.angle = random.randint(0, 360)
        self.speed = random.uniform(speed_range[0], speed_range[1])

    def update(self):
        self.x += math.cos(
            math.radians(self.angle)
        ) * self.speed

        self.y -= math.sin(
            math.radians(self.angle)
        ) * self.speed

        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            WHITE,
            (int(self.x), int(self.y)),
            self.radius,
            2,
        )


# --------------------------------------------------
# Collision detection
# --------------------------------------------------
def check_collision(obj1, obj2):
    distance = math.hypot(
        obj1.x - obj2.x,
        obj1.y - obj2.y,
    )

    return distance < obj1.radius + obj2.radius


# --------------------------------------------------
# Main game
# --------------------------------------------------
def main():
    player = Player()
    bullets = []
    asteroids = []
    pace_mgr = PaceManager()

    score = 0
    lives = MAX_LIVES
    last_lost_time = None
    game_state = "start"

    button_rect = pygame.Rect(
        WIDTH // 2 - 80,
        HEIGHT // 2 + 50,
        160,
        45,
    )

    def spawn_initial_asteroids():
        asteroids.clear()
        count = pace_mgr.get_spawn_count(score)
        speed_range = pace_mgr.get_asteroid_speed_range()

        for _ in range(count):
            x = random.choice([
                random.randint(0, WIDTH // 3),
                random.randint(WIDTH * 2 // 3, WIDTH),
            ])

            y = random.choice([
                random.randint(0, HEIGHT // 3),
                random.randint(HEIGHT * 2 // 3, HEIGHT),
            ])

            asteroids.append(Asteroid(x, y, 3, speed_range))

    def reset_game():
        nonlocal player, bullets, score
        nonlocal lives, last_lost_time, game_state

        player = Player()
        bullets.clear()
        score = 0
        lives = MAX_LIVES
        last_lost_time = None
        game_state = "playing"
        pace_mgr.reset()

        spawn_initial_asteroids()

    while True:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # ------------------------------
        # Handle events
        # ------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if arduino:
                    arduino.close()

                pygame.quit()
                sys.exit()

            if game_state == "start":
                if start_screen.handle_event(event):
                    game_state = "playing"
                    spawn_initial_asteroids()

            elif game_state == "playing":
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_SPACE
                ):
                    tip_x = player.x + math.cos(
                        math.radians(player.angle)
                    ) * player.radius * 2

                    tip_y = player.y - math.sin(
                        math.radians(player.angle)
                    ) * player.radius * 2

                    bullets.append(
                        Bullet(
                            tip_x,
                            tip_y,
                            player.angle,
                        )
                    )

            elif game_state == "game_over":
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_r
                ):
                    reset_game()

                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and button_rect.collidepoint(event.pos)
                ):
                    reset_game()

        # ------------------------------
        # Start screen
        # ------------------------------
        if game_state == "start":
            start_screen.draw(screen)
            continue

        # ------------------------------
        # Update gameplay
        # ------------------------------
        if game_state == "playing":
            player.update()
            pace_mgr.update(player)

            # Update bullets.
            for bullet in bullets[:]:
                bullet.update()

                if (
                    bullet.x < 0
                    or bullet.x > WIDTH
                    or bullet.y < 0
                    or bullet.y > HEIGHT
                ):
                    bullets.remove(bullet)

            # Update asteroids and check collisions.
            for asteroid in asteroids[:]:
                asteroid.update()

                if (
                    not player.is_invulnerable()
                    and check_collision(player, asteroid)
                ):
                    lives -= 1
                    last_lost_time = pygame.time.get_ticks()

                    if asteroid in asteroids:
                        asteroids.remove(asteroid)

                    if lives <= 0:
                        game_state = "game_over"
                        break

                    player = Player()
                    player.invulnerable_until = (
                        pygame.time.get_ticks()
                        + INVULNERABILITY_MS
                    )
                    break

                for bullet in bullets[:]:
                    if check_collision(bullet, asteroid):
                        score += asteroid.size * 10

                        if bullet in bullets:
                            bullets.remove(bullet)

                        if asteroid in asteroids:
                            asteroids.remove(asteroid)

                        if asteroid.size > 1:
                            speed_range = pace_mgr.get_asteroid_speed_range()
                            asteroids.append(
                                Asteroid(
                                    asteroid.x,
                                    asteroid.y,
                                    asteroid.size - 1,
                                    speed_range,
                                )
                            )

                            asteroids.append(
                                Asteroid(
                                    asteroid.x,
                                    asteroid.y,
                                    asteroid.size - 1,
                                    speed_range,
                                )
                            )

                        break

            if game_state == "playing" and not asteroids:
                spawn_initial_asteroids()

        # ------------------------------
        # Draw frame
        # ------------------------------
        screen.fill(BLACK)

        if game_state == "playing":
            player.draw(screen)

            for bullet in bullets:
                bullet.draw(screen)

            for asteroid in asteroids:
                asteroid.draw(screen)

        elif game_state == "game_over":
            game_over_text = font.render(
                "GAME OVER", True, RED
            )

            screen.blit(
                game_over_text,
                (
                    WIDTH // 2
                    - game_over_text.get_width() // 2,
                    HEIGHT // 2 - 80,
                ),
            )

            final_score = font.render(
                f"Final Score: {score}", True, WHITE
            )

            screen.blit(
                final_score,
                (
                    WIDTH // 2
                    - final_score.get_width() // 2,
                    HEIGHT // 2 - 35,
                ),
            )

            button_color = (
                LIGHT_GRAY
                if button_rect.collidepoint(mouse_pos)
                else GRAY
            )

            pygame.draw.rect(
                screen,
                button_color,
                button_rect,
                border_radius=8,
            )

            pygame.draw.rect(
                screen,
                WHITE,
                button_rect,
                2,
                border_radius=8,
            )

            button_text = button_font.render(
                "PLAY AGAIN", True, BLACK
            )

            screen.blit(
                button_text,
                button_text.get_rect(
                    center=button_rect.center
                ),
            )

        # ------------------------------
        # HUD
        # ------------------------------
        score_text = font.render(
            f"Score: {score}", True, WHITE
        )

        screen.blit(score_text, (10, 10))

        draw_lives(
            screen,
            lives,
            last_lost_time,
        )

        pygame.display.flip()


if __name__ == "__main__":
    main()