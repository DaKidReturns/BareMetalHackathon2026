import os
import pygame


class StartScreen:
    """Neon start screen using the Asteroids asset pack."""

    def __init__(self, width, height, asset_dir=None):
        self.width = width
        self.height = height

        self.black = (3, 5, 18)
        self.white = (235, 245, 255)
        self.cyan = (60, 210, 255)
        self.blue = (35, 95, 210)
        self.gray = (150, 170, 195)
        self.light_gray = (205, 220, 240)

        # Assets are resolved relative to this file.
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.asset_dir = asset_dir or os.path.join(project_dir, "assets")

        self.background = self._load_image(
            os.path.join(self.asset_dir, "backgrounds", "nebula.jpg"),
            alpha=False,
        )
        if self.background:
            self.background = pygame.transform.smoothscale(
                self.background, (self.width, self.height)
            )

        self.ship_image = self._load_image(
            os.path.join(self.asset_dir, "player", "ship_idle.png"),
            alpha=True,
        )
        if self.ship_image:
            self.ship_image = pygame.transform.smoothscale(
                self.ship_image, (96, 96)
            )

        self.title_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 20)
        self.button_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 15)

        self.start_button = pygame.Rect(
            width // 2 - 110, height // 2 + 75, 220, 50
        )

        self.stars = [
            (90, 100), (180, 170), (690, 110), (620, 210),
            (120, 430), (700, 450), (350, 120), (520, 480),
            (270, 500), (60, 300), (740, 260), (440, 80),
        ]

        self.star_surface = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        for i, (x, y) in enumerate(self.stars):
            radius = 2 if i % 3 == 0 else 1
            pygame.draw.circle(
                self.star_surface,
                (110, 205, 255, 180 if radius == 2 else 120),
                (x % self.width, y % self.height),
                radius,
            )

        self.overlay = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.overlay.fill((0, 3, 18, 95))

    @staticmethod
    def _load_image(path, alpha):
        try:
            image = pygame.image.load(path)
            return image.convert_alpha() if alpha else image.convert()
        except (pygame.error, OSError):
            print(f"Asset not found or could not load: {path}")
            return None

    def handle_event(self, event):
        """Return True when the player chooses to start."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.start_button.collidepoint(event.pos):
                return True

        return False

    def draw(self, screen):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(self.black)

        screen.blit(self.overlay, (0, 0))
        screen.blit(self.star_surface, (0, 0))

        cx = self.width // 2
        if self.ship_image:
            screen.blit(
                self.ship_image,
                self.ship_image.get_rect(center=(cx, 145)),
            )
        else:
            points = [
                (cx, 100), (cx - 22, 160),
                (cx, 150), (cx + 22, 160),
            ]
            pygame.draw.polygon(screen, self.cyan, points, 2)

        title_glow = self.title_font.render("ASTEROIDS", True, self.blue)
        title = self.title_font.render("ASTEROIDS", True, self.cyan)
        title_rect = title.get_rect(center=(cx, 245))
        glow_rect = title_glow.get_rect(center=(cx, 245))
        screen.blit(title_glow, (glow_rect.x - 2, glow_rect.y + 2))
        screen.blit(title, title_rect)

        subtitle = self.subtitle_font.render(
            "SURVIVE. SHOOT. SCORE.", True, self.white
        )
        screen.blit(subtitle, subtitle.get_rect(center=(cx, 295)))

        hovered = self.start_button.collidepoint(pygame.mouse.get_pos())
        fill = (35, 105, 160) if hovered else (7, 20, 48)
        border = (125, 235, 255) if hovered else self.cyan

        pygame.draw.rect(screen, fill, self.start_button, border_radius=9)
        pygame.draw.rect(
            screen, border, self.start_button, width=2, border_radius=9
        )

        button_text = self.button_font.render(
            "START GAME", True, self.white if hovered else self.cyan
        )
        screen.blit(
            button_text, button_text.get_rect(center=self.start_button.center)
        )

        controls = self.small_font.render(
            "LEFT / RIGHT: ROTATE   UP: THRUST   SPACE: SHOOT",
            True, self.light_gray,
        )
        screen.blit(controls, controls.get_rect(center=(cx, 465)))

        hint = self.small_font.render(
            "PRESS ENTER OR CLICK START", True, self.gray
        )
        screen.blit(hint, hint.get_rect(center=(cx, 495)))
