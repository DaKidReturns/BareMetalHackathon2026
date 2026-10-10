Neon Asteroids Asset Pack
=========================

Folder structure:
- backgrounds/nebula.jpg : 1280x720 space background (JPEG)
- player/ship_idle.png, ship_left.png, ship_right.png, ship_thrust.png : transparent ship sprites
- player/thrust/thrust_0.png ... thrust_7.png : thrust animation frames
- asteroids/large, medium, small : transparent asteroid sprites
- projectiles/ : blue/red/green bullets and impact particle
- explosions/explosion_0.png ... explosion_7.png : transparent explosion frames
- effects/ : hit spark, star particles, power-up icon

Pygame notes:
- Load files once at startup with pygame.image.load(...).convert_alpha()
- Use pygame.transform.rotate(surface, angle) for ship rotation; cache rotated surfaces if possible.
- Scale the background once to your display size.
- Animation frames are individual PNGs; alpha transparency is preserved.
- This pack contains artwork assets, not game code.

Example:
    import os, pygame
    ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")
    ship = pygame.image.load(os.path.join(ASSET_DIR, "player", "ship_idle.png")).convert_alpha()
    background = pygame.image.load(os.path.join(ASSET_DIR, "backgrounds", "nebula.jpg")).convert()
