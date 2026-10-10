import math
import os
import random
import sys

import pygame

try:
    import serial
except ImportError:
    serial = None

from start_screen import StartScreen
from pace_manager import PaceManager
from score_manager import ScoreManager


pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
MAX_LIVES = 3
INVULNERABILITY_MS = 2000
LIFE_FLASH_MS = 600

BLACK = (3, 5, 18)
WHITE = (235, 245, 255)
RED = (255, 65, 100)
GRAY = (120, 145, 175)
LIGHT_GRAY = (205, 220, 240)
CYAN = (60, 210, 255)

LARGE_ASTEROID_RADIUS = 40
MEDIUM_ASTEROID_RADIUS = 20
SMALL_ASTEROID_RADIUS = 10

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(PROJECT_DIR, "assets")


def load_image(relative_path, alpha=True):
    """Load an asset, returning None if it is absent or unreadable."""
    path = os.path.join(ASSET_DIR, relative_path)
    try:
        image = pygame.image.load(path)
        # Assets are loaded at module startup, before set_mode() creates a
        # display surface. convert()/convert_alpha() require a display, so
        # only use them when one already exists.
        if pygame.display.get_surface() is not None:
            return image.convert_alpha() if alpha else image.convert()
        return image
    except (pygame.error, OSError) as exc:
        print(f"Asset missing/unreadable (using fallback): {path} ({exc})")
        return None


def load_scaled(relative_path, size):
    image = load_image(relative_path)
    if image is not None:
        return pygame.transform.smoothscale(image, (size, size))
    return None


# Load assets once at startup.
background_image = load_image("", alpha=False)
if background_image is not None:
    background_image = pygame.transform.smoothscale(
        background_image, (WIDTH, HEIGHT)
    )

ship_image = load_image("player/ship_idle.png")
thrust_image = load_image("player/ship_thrust.png")
if ship_image is not None:
    ship_image = pygame.transform.smoothscale(ship_image, (64, 64))
if thrust_image is not None:
    thrust_image = pygame.transform.smoothscale(thrust_image, (64, 64))

asteroid_images = {
    3: [
        load_scaled(f"asteroids/large/asteroid_large_{i}.png", 88)
        for i in range(1, 5)
    ],
    2: [
        load_scaled(f"asteroids/medium/asteroid_medium_{i}.png", 48)
        for i in range(1, 4)
    ],
    1: [
        load_scaled(f"asteroids/small/asteroid_small_{i}.png", 28)
        for i in range(1, 4)
    ],
}
for size in asteroid_images:
    asteroid_images[size] = [image for image in asteroid_images[size] if image]

bullet_image = load_image("projectiles/bullet_red.png")
if bullet_image is not None:
    bullet_image = pygame.transform.smoothscale(bullet_image, (10, 24))

explosion_images = [
    load_image(f"explosions/explosion_{i}.png") for i in range(8)
]
explosion_images = [image for image in explosion_images if image]

# Optional serial controller. Set ASTEROIDS_SERIAL_PORT to the actual port.
# Keyboard controls always remain available.
arduino = None
serial_port = os.environ.get("ASTEROIDS_SERIAL_PORT")
if serial_port and serial is not None:
    try:
        arduino = serial.Serial(serial_port, 9600, timeout=0)
        print(f"Controller connected on {serial_port}")
    except (serial.SerialException, OSError) as exc:
        print(f"Controller unavailable ({exc}); using keyboard controls.")
else:
    print("No serial controller configured; using keyboard controls.")


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON ASTEROIDS")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, bold=True)
small_font = pygame.font.SysFont("Arial", 16)
button_font = pygame.font.SysFont("Arial", 20, bold=True)
start_screen = StartScreen(WIDTH, HEIGHT)


def get_ship_points(x, y, angle, radius):
    """Triangle points used for collision-friendly HUD/fallback drawing."""
    tip_x = x + math.cos(math.radians(angle)) * radius * 2
    tip_y = y - math.sin(math.radians(angle)) * radius * 2
    left_x = x + math.cos(math.radians(angle + 130)) * radius
    left_y = y - math.sin(math.radians(angle + 130)) * radius
    right_x = x + math.cos(math.radians(angle - 130)) * radius
    right_y = y - math.sin(math.radians(angle - 130)) * radius
    return [
        (int(tip_x), int(tip_y)),
        (int(left_x), int(left_y)),
        (int(right_x), int(right_y)),
    ]


def draw_lives(surface, lives, last_lost_time):
    now = pygame.time.get_ticks()
    start_x, y, spacing, icon_radius = WIDTH - 105, 28, 35, 7

    for index in range(MAX_LIVES):
        x = start_x + index * spacing
        points = get_ship_points(x, y, 90, icon_radius)
        if index < lives:
            pygame.draw.polygon(surface, CYAN, points, 2)
        elif (
            index == lives
            and last_lost_time is not None
            and now - last_lost_time < LIFE_FLASH_MS
        ):
            pygame.draw.polygon(surface, RED, points)
        else:
            pygame.draw.polygon(surface, GRAY, points, 2)


class Player:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.angle = 90
        self.speed = 0.0
        self.radius = 15
        self.invulnerable_until = 0
        self.thrusting = False

    def is_invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    def draw(self, surface):
        if self.is_invulnerable() and (pygame.time.get_ticks() // 120) % 2 == 0:
            return

        image = thrust_image if self.thrusting and thrust_image else ship_image
        if image is not None:
            # The supplied sprite points up; angle 90 means up in game coordinates.
            rotated = pygame.transform.rotate(image, self.angle - 90)
            surface.blit(rotated, rotated.get_rect(center=(round(self.x), round(self.y))))
        else:
            pygame.draw.polygon(
                surface, CYAN,
                get_ship_points(self.x, self.y, self.angle, self.radius), 2
            )

    def update(self):
        self.thrusting = False

        # Optional controller protocol: "x,y\n" integer pairs.
        if arduino:
            try:
                while arduino.in_waiting:
                    raw = arduino.readline().decode("utf-8", errors="ignore").strip()
                    if "," not in raw:
                        continue
                    x_text, y_text = raw.split(",", 1)
                    x_val, y_val = int(x_text), int(y_text)
                    if x_val < -5:
                        self.angle += 5
                    elif x_val > 5:
                        self.angle -= 5
                    if y_val > 5:
                        self.speed = min(self.speed + 0.15, 5)
                        self.thrusting = True
            except (ValueError, OSError):
                pass

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.angle += 4
        if keys[pygame.K_RIGHT]:
            self.angle -= 4
        if keys[pygame.K_UP]:
            self.speed = min(self.speed + 0.15, 5)
            self.thrusting = True
        else:
            self.speed *= 0.985

        self.x = (self.x + math.cos(math.radians(self.angle)) * self.speed) % WIDTH
        self.y = (self.y - math.sin(math.radians(self.angle)) * self.speed) % HEIGHT


class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 4

    def update(self):
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y -= math.sin(math.radians(self.angle)) * self.speed

    def draw(self, surface):
        if bullet_image is not None:
            rotated = pygame.transform.rotate(bullet_image, self.angle - 90)
            surface.blit(rotated, rotated.get_rect(center=(round(self.x), round(self.y))))
        else:
            pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y)), self.radius)


class Asteroid:
    def __init__(self, x, y, size, speed_range=(1.0, 3.0)):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.radius = {
            3: LARGE_ASTEROID_RADIUS,
            2: MEDIUM_ASTEROID_RADIUS,
            1: SMALL_ASTEROID_RADIUS,
        }[size]
        self.direction = random.randint(0, 359)
        self.speed = random.uniform(*speed_range)
        choices = asteroid_images.get(size, [])
        self.image = random.choice(choices) if choices else None
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-1.2, 1.2)

    def update(self):
        self.x = (self.x + math.cos(math.radians(self.direction)) * self.speed) % WIDTH
        self.y = (self.y - math.sin(math.radians(self.direction)) * self.speed) % HEIGHT
        self.rotation = (self.rotation + self.rotation_speed) % 360

    def draw(self, surface):
        if self.image is not None:
            rotated = pygame.transform.rotate(self.image, self.rotation)
            surface.blit(rotated, rotated.get_rect(center=(round(self.x), round(self.y))))
        else:
            pygame.draw.circle(
                surface, CYAN, (int(self.x), int(self.y)), self.radius, 2
            )


class Explosion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.start_time = pygame.time.get_ticks()
        self.duration = 450

    def update(self):
        return pygame.time.get_ticks() - self.start_time < self.duration

    def draw(self, surface):
        elapsed = pygame.time.get_ticks() - self.start_time
        if explosion_images:
            frame_index = min(
                len(explosion_images) - 1,
                int(elapsed / self.duration * len(explosion_images)),
            )
            image = explosion_images[frame_index]
            surface.blit(image, image.get_rect(center=(round(self.x), round(self.y))))
        else:
            radius = max(2, int(24 * (1 - elapsed / self.duration)))
            pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), radius, 2)


def check_collision(obj1, obj2):
    return math.hypot(obj1.x - obj2.x, obj1.y - obj2.y) < obj1.radius + obj2.radius


def draw_background():
    if background_image is not None:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(BLACK)
        for _ in range(35):
            pygame.draw.circle(
                screen, (70, 110, 160),
                (random.randrange(WIDTH), random.randrange(HEIGHT)), 1
            )


def main():
    player = Player()
    bullets = []
    asteroids = []
    explosions = []
    pace_mgr = PaceManager()
    score_mgr = ScoreManager()

    score = 0
    lives = MAX_LIVES
    last_lost_time = None
    game_state = "start"
    button_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 50, 160, 45)

    def spawn_initial_asteroids():
        asteroids.clear()
        count = pace_mgr.get_spawn_count(score)
        speed_range = pace_mgr.get_asteroid_speed_range()
        for _ in range(count):
            x = random.choice([
                random.randint(0, WIDTH // 3),
                random.randint(WIDTH * 2 // 3, WIDTH - 1),
            ])
            y = random.choice([
                random.randint(0, HEIGHT // 3),
                random.randint(HEIGHT * 2 // 3, HEIGHT - 1),
            ])
            asteroids.append(Asteroid(x, y, 3, speed_range))

    def reset_game():
        nonlocal player, score, lives, last_lost_time, game_state
        player = Player()
        bullets.clear()
        explosions.clear()
        score = 0
        lives = MAX_LIVES
        last_lost_time = None
        game_state = "playing"
        pace_mgr.reset()
        spawn_initial_asteroids()

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game_state == "start":
                if start_screen.handle_event(event):
                    game_state = "playing"
                    spawn_initial_asteroids()
            elif game_state in ("playing", "paused"):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        game_state = "paused" if game_state == "playing" else "playing"
                    elif event.key == pygame.K_SPACE and game_state == "playing":
                        tip_x = player.x + math.cos(math.radians(player.angle)) * player.radius * 2
                        tip_y = player.y - math.sin(math.radians(player.angle)) * player.radius * 2
                        bullets.append(Bullet(tip_x, tip_y, player.angle))
            elif game_state == "game_over":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    reset_game()
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and button_rect.collidepoint(event.pos)
                ):
                    reset_game()

        if game_state == "start":
            start_screen.draw(screen)
            pygame.display.flip()
            continue

        if game_state == "playing":
            player.update()
            pace_mgr.update(player)

            for bullet in bullets[:]:
                bullet.update()
                if bullet.x < 0 or bullet.x > WIDTH or bullet.y < 0 or bullet.y > HEIGHT:
                    bullets.remove(bullet)

            for explosion in explosions[:]:
                if not explosion.update():
                    explosions.remove(explosion)

            for asteroid in asteroids[:]:
                asteroid.update()

                if not player.is_invulnerable() and check_collision(player, asteroid):
                    lives -= 1
                    last_lost_time = pygame.time.get_ticks()
                    explosions.append(Explosion(asteroid.x, asteroid.y))
                    if asteroid in asteroids:
                        asteroids.remove(asteroid)

                    if lives <= 0:
                        score_mgr.save_high_score(score)
                        game_state = "game_over"
                        break

                    player = Player()
                    player.invulnerable_until = pygame.time.get_ticks() + INVULNERABILITY_MS
                    break

                for bullet in bullets[:]:
                    if check_collision(bullet, asteroid):
                        score += asteroid.size * 10
                        explosions.append(Explosion(asteroid.x, asteroid.y))
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if asteroid in asteroids:
                            asteroids.remove(asteroid)

                        if asteroid.size > 1:
                            speed_range = pace_mgr.get_asteroid_speed_range()
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1, speed_range))
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1, speed_range))
                        break

            if game_state == "playing" and not asteroids:
                spawn_initial_asteroids()

        draw_background()

        if game_state in ("playing", "paused"):
            for asteroid in asteroids:
                asteroid.draw(screen)
            for bullet in bullets:
                bullet.draw(screen)
            for explosion in explosions:
                explosion.draw(screen)
            player.draw(screen)

            if game_state == "paused":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 12, 170))
                screen.blit(overlay, (0, 0))
                pause_text = font.render("PAUSED - Press P to Resume", True, CYAN)
                screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        elif game_state == "game_over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 12, 160))
            screen.blit(overlay, (0, 0))
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
            final_score = font.render(f"Final Score: {score}", True, WHITE)
            screen.blit(final_score, final_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55)))
            high_score_text = small_font.render(
                f"High Score: {score_mgr.high_score}", True, LIGHT_GRAY
            )
            screen.blit(high_score_text, high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

            hovered = button_rect.collidepoint(mouse_pos)
            button_color = (35, 105, 160) if hovered else (7, 20, 48)
            pygame.draw.rect(screen, button_color, button_rect, border_radius=8)
            pygame.draw.rect(screen, CYAN, button_rect, 2, border_radius=8)
            again = button_font.render("PLAY AGAIN", True, WHITE if hovered else CYAN)
            screen.blit(again, again.get_rect(center=button_rect.center))

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        high_score_hud = small_font.render(f"High: {score_mgr.high_score}", True, LIGHT_GRAY)
        screen.blit(high_score_hud, (10, 40))
        draw_lives(screen, lives, last_lost_time)

        pygame.display.flip()

    if arduino:
        arduino.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
