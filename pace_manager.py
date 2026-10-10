import math

class PaceManager:
    def __init__(self):
        # Base settings
        self.base_speed_min = 1.0
        self.base_speed_max = 3.0
        self.base_asteroid_count = 5

        # Player tracking metrics
        self.prev_x = None
        self.prev_y = None
        self.prev_angle = None
        
        # Smooth activity score (0.0 to 1.0+)
        self.activity_score = 0.0

    def update(self, player):
        """Analyzes player movement intensity to update pacing metrics."""
        if self.prev_x is None:
            self.prev_x, self.prev_y, self.prev_angle = player.x, player.y, player.angle
            return

        # Calculate positional displacement
        distance_moved = math.hypot(player.x - self.prev_x, player.y - self.prev_y)
        # Avoid huge spikes when wrapping around screen edges
        if distance_moved > 100:
            distance_moved = player.speed

        # Calculate rotational movement
        angle_change = abs(player.angle - self.prev_angle)

        # Immediate activity level based on current frame actions
        current_activity = (distance_moved / 5.0) * 0.6 + (angle_change / 5.0) * 0.4

        # Smooth activity index using Exponential Moving Average
        self.activity_score = (self.activity_score * 0.95) + (current_activity * 0.05)

        # Update historical state
        self.prev_x, self.prev_y, self.prev_angle = player.x, player.y, player.angle

    def get_asteroid_speed_range(self):
        """Returns min and max speed for new asteroids based on activity."""
        multiplier = 1.0 + (self.activity_score * 0.8)
        return self.base_speed_min * multiplier, self.base_speed_max * multiplier

    def get_spawn_count(self, score):
        """Calculates asteroid spawn count based on activity score and overall score."""
        activity_bonus = int(self.activity_score * 2)
        score_bonus = score // 100
        return self.base_asteroid_count + activity_bonus + score_bonus

    def reset(self):
        """Resets dynamic tracking metrics on game reset."""
        self.prev_x = None
        self.prev_y = None
        self.prev_angle = None
        self.activity_score = 0.0