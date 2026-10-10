import os

class ScoreManager:
    def __init__(self, filename="high_score.txt"):
        self.filename = filename
        self.high_score = self.load_high_score()

    def load_high_score(self):
        """Loads the high score from a local text file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

    def save_high_score(self, current_score):
        """Updates and saves the high score if the current score is higher."""
        if current_score > self.high_score:
            self.high_score = current_score
            try:
                with open(self.filename, "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                pass
        return self.high_score