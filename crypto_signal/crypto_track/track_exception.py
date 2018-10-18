class TrackException(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status

    def __str__(self):
        return f"{self.status}: {self.message}"
