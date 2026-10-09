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

# Astorid Sizes
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

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 90
        self.speed = 0
        self.radius = 15

    def draw(self, surface):
        # Calculate the 3 points of the triangle based on current angle
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

                        # --- NEW I2C MAP TO GAME MOVEMENT ---
                        # MMA7660 range is roughly -32 to 31. Resting is 0.
                        # Deadzone is set between -5 and 5 to prevent jitter.
                        
                        # Tilt Left / Right to rotate
                        if x_val < -5:     
                            self.angle += 5
                        elif x_val > 5:   
                            self.angle -= 5
                            
                        # Tilt Forward to thrust
                        # Note: Depending on which way the chip faces you, 
                        # you may need to change this to 'y_val < -5'
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

    def spawn_initial_asteroids():
        asteroids.clear()
        # Initial asteroids
        for _ in range(5):
            # Spawn away from player
            x = random.choice([random.randint(0, WIDTH//3), random.randint(WIDTH*2//3, WIDTH)])
            y = random.choice([random.randint(0, HEIGHT//3), random.randint(HEIGHT*2//3, HEIGHT)])
            asteroids.append(Asteroid(x, y, 3))
    
    spawn_initial_asteroids()

    while True:
        clock.tick(FPS)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN :
                if not game_over:
                    if event.key == pygame.K_SPACE:
                        # Shoot bullet from the tip of the ship
                        tip_x = player.x + math.cos(math.radians(player.angle)) * player.radius * 2
                        tip_y = player.y - math.sin(math.radians(player.angle)) * player.radius * 2
                        bullets.append(Bullet(tip_x, tip_y, player.angle))
                else: 
                    if event.key == pygame.K_r:
                        player = Player()      # Reset player
                        bullets.clear()        # Clear screen of old bullets
                        score = 0              # Reset score
                        game_over = False      # Resume game
                        spawn_initial_asteroids() # Respawn enemies

        if not game_over:
            # Update Objects
            player.update()
            
            for bullet in bullets[:]:
                bullet.update()
                # Remove bullets off screen
                if bullet.x < 0 or bullet.x > WIDTH or bullet.y < 0 or bullet.y > HEIGHT:
                    bullets.remove(bullet)

            for asteroid in asteroids[:]:
                asteroid.update()
                
                # Check collision with player
                if check_collision(player, asteroid):
                    game_over = True

                # Check collision with bullets
                for bullet in bullets[:]:
                    if check_collision(bullet, asteroid):
                        score += asteroid.size * 10
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if asteroid in asteroids:
                            asteroids.remove(asteroid)
                            
                        # Break into smaller asteroids
                        if asteroid.size > 1:
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1))
                            asteroids.append(Asteroid(asteroid.x, asteroid.y, asteroid.size - 1))
                        break

            # Spawn new asteroids if all are destroyed
            if len(asteroids) == 0:
                for _ in range(5):
                    x = random.choice([random.randint(0, WIDTH//3), random.randint(WIDTH*2//3, WIDTH)])
                    y = random.choice([random.randint(0, HEIGHT//3), random.randint(HEIGHT*2//3, HEIGHT)])
                    asteroids.append(Asteroid(x, y, 3))

        # Draw Objects
        if not game_over:
            player.draw(screen)
        else:
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH//2 - 70, HEIGHT//2))

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