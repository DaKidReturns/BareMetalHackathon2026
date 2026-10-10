
import pygame


class StartScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.green = (80, 255, 170)
        self.gray = (150, 150, 150)
        self.light_gray = (220, 220, 220)

        self.title_font = pygame.font.SysFont(
            "Arial", 56, bold=True
        )
        self.subtitle_font = pygame.font.SysFont(
            "Arial", 20
        )
        self.button_font = pygame.font.SysFont(
            "Arial", 22, bold=True
        )
        self.small_font = pygame.font.SysFont(
            "Arial", 16
        )

        self.start_button = pygame.Rect(
            width // 2 - 110,
            height // 2 + 55,
            220,
            50,
        )

        # Decorative stars stay in fixed positions.
        self.stars = [
            (90, 100), (180, 170), (690, 110),
            (620, 210), (120, 430), (700, 450),
            (350, 120), (520, 480), (270, 500),
        ]

    def handle_event(self, event):
        """Return True when the player chooses to start."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1
                and self.start_button.collidepoint(event.pos)
            ):
                return True

        return False

    def draw(self, screen):
        screen.fill(self.black)

        # Background stars
        for x, y in self.stars:
            pygame.draw.circle(
                screen, self.white, (x, y), 2
            )

        # Wireframe spaceship
        cx = self.width // 2
        ship_points = [
            (cx, 145),
            (cx - 15, 180),
            (cx, 172),
            (cx + 15, 180),
        ]
        pygame.draw.polygon(
            screen, self.white, ship_points, 2
        )

        # Game title
        title = self.title_font.render(
            "ASTEROIDS", True, self.green
        )
        screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 235)
            ),
        )

        subtitle = self.subtitle_font.render(
            "SURVIVE. SHOOT. SCORE.",
            True,
            self.white,
        )
        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(self.width // 2, 290)
            ),
        )

        # Start button with hover effect
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.start_button.collidepoint(mouse_pos)
        button_color = (
            self.green if hovered else (25, 45, 38)
        )

        pygame.draw.rect(
            screen,
            button_color,
            self.start_button,
            border_radius=8,
        )
        pygame.draw.rect(
            screen,
            self.green,
            self.start_button,
            width=2,
            border_radius=8,
        )

        button_text = self.button_font.render(
            "START GAME", True, self.black if hovered else self.green
        )
        screen.blit(
            button_text,
            button_text.get_rect(
                center=self.start_button.center
            ),
        )

        controls = self.small_font.render(
            "LEFT / RIGHT: ROTATE   UP: THRUST   SPACE: SHOOT",
            True,
            self.light_gray,
        )
        screen.blit(
            controls,
            controls.get_rect(
                center=(self.width // 2, 440)
            ),
        )

        pygame.display.flip()
