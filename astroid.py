import pygame
import random
import math
import sys
import serial 

# Initialize Pygame
pygame.init()

# Game Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)

# Asteroid Sizes
LARGE_ASTROID = 40
MEDIUM_ASTROID = 20
SMALL_ASTROID = 10 

ASTROID_SPEED = 10

try:
    arduino = serial.Serial('/dev/cu.usbmodem13201', 9600, timeout=0)
except serial.SerialException:
    print("Microcontroller not found.")
    arduino = None

# Setup Display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Asteroids Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, bold=True)
button_font = pygame.font.SysFont("Arial", 20, bold=True)

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 90
        self.speed = 0
        self.radius = 15

    def draw(self, surface):
        tip_x = self.x + math.cos(math.radians(self.angle)) * self.radius * 2
        tip_y = self.y - math.sin(math.radians(self.angle)) * self.radius * 2
        
        bl_x = self.x + math.cos(math.radians(self.angle + 130)) * self.radius
        bl_y = self.y - math.sin(math.radians(self.angle + 130)) * self.radius
        
        br_x = self.x + math.cos(math.radians(self.angle - 130)) * self.radius
        br_y = self.y - math.sin(math.radians(self.angle - 130)) * self.radius

        pygame.draw.polygon(surface, WHITE, [(tip_x, tip_y), (bl_x, bl_y), (br_x, br_y)], 2)

    def update(self):
        if arduino:
            while arduino.in_waiting > 0:
                try:
                    raw_data = arduino.readline().decode('utf-8').strip()
                    
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
        
        # Rotation
        if keys[pygame.K_LEFT]:
            self.angle += 5
        if keys[pygame.K_RIGHT]:
            self.angle -= 5
            
        # Thrust
        if keys[pygame.K_UP]:
            self.speed = 5
        else:
            self.speed = 0

        # Movement
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y -= math.sin(math.radians(self.angle)) * self.speed

        # Screen Wrap
        self.x %= WIDTH
        self.y %= HEIGHT

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 3

    def update(self):
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y -= math.sin(math.radians(self.angle)) * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)

class Asteroid:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size # 3: Large, 2: Medium, 1: Small
        
        if size == 3: self.radius = LARGE_ASTROID
        elif size == 2: self.radius = MEDIUM_ASTROID
        else: self.radius = SMALL_ASTROID
            
        self.angle = random.randint(0, 360)
        self.speed = random.uniform(1, 3)

    def update(self):
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y -= math.sin(math.radians(self.angle)) * self.speed
        
        # Screen Wrap
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

def check_collision(obj1, obj2):
    distance = math.hypot(obj1.x - obj2.x, obj1.y - obj2.y)
    return distance < (obj1.radius + obj2.radius)

def main():
    player = Player()
    bullets = []
    asteroids = []
    score = 0
    game_over = False

    # Define Restart Button Dimensions & Position
    button_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 50, 160, 45)

    def reset_game():
        nonlocal player, bullets, score, game_over
        player = Player()
        bullets.clear()
        score = 0
        game_over = False
        spawn_initial_asteroids()

    def spawn_initial_asteroids():
        asteroids.clear()
        for _ in range(5):
            x = random.choice([random.randint(0, WIDTH//3), random.randint(WIDTH*2//3, WIDTH)])
            y = random.choice([random.randint(0, HEIGHT//3), random.randint(HEIGHT*2//3, HEIGHT)])
            asteroids.append(Asteroid(x, y, 3))
    
    spawn_initial_asteroids()

    while True:
        clock.tick(FPS)
        screen.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key == pygame.K_SPACE:
                        tip_x = player.x + math.cos(math.radians(player.angle)) * player.radius * 2
                        tip_y = player.y - math.sin(math.radians(player.angle)) * player.radius * 2
                        bullets.append(Bullet(tip_x, tip_y, player.angle))
                else: 
                    if event.key == pygame.K_r:
                        reset_game()

            # Detect Mouse Click on the Play Again Button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over and button_rect.collidepoint(mouse_pos):
                    reset_game()

        if not game_over:
            player.update()
            
            for bullet in bullets[:]:
                bullet.update()
                if bullet.x < 0 or bullet.x > WIDTH or bullet.y < 0 or bullet.y > HEIGHT:
                    bullets.remove(bullet)

            for asteroid in asteroids[:]:
                asteroid.update()
                
                if check_collision(player, asteroid):
                    game_over = True

                for bullet in bullets[:]:
                    if check_collision(bullet, asteroid):
                        score += asteroid.size * 10
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if asteroid in asteroids:
                            asteroids.remove(asteroid)
                            
                        if asteroid.size > 1:
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1))
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1))
                        break

            if len(asteroids) == 0:
                for _ in range(5):
                    x = random.choice([random.randint(0, WIDTH//3), random.randint(WIDTH*2//3, WIDTH)])
                    y = random.choice([random.randint(0, HEIGHT//3), random.randint(HEIGHT*2//3, HEIGHT)])
                    asteroids.append(Asteroid(x, y, 3))

        # Draw Entities
        if not game_over:
            player.draw(screen)
        else:
            # Draw Game Over Text
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 40))

            # Draw Play Again Button with hover effect
            button_color = LIGHT_GRAY if button_rect.collidepoint(mouse_pos) else GRAY
            pygame.draw.rect(screen, button_color, button_rect, border_radius=8)
            pygame.draw.rect(screen, WHITE, button_rect, 2, border_radius=8) # Border

            button_text = button_font.render("PLAY AGAIN", True, BLACK)
            text_x = button_rect.x + (button_rect.width - button_text.get_width()) // 2
            text_y = button_rect.y + (button_rect.height - button_text.get_height()) // 2
            screen.blit(button_text, (text_x, text_y))

        for bullet in bullets:
            bullet.draw(screen)
            
        for asteroid in asteroids:
            asteroid.draw(screen)

        # Draw UI
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()

if __name__ == "__main__":
    main()