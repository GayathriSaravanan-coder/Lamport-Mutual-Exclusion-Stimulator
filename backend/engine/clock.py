class LamportClock:
    """Lamport logical clock."""

    def __init__(self, value: int = 0):
        self.value = value

    def tick(self) -> int:
        """Local event: clock = clock + 1."""
        self.value += 1
        return self.value

    def update(self, received: int) -> int:
        """Receive event: clock = max(local, received) + 1."""
        self.value = max(self.value, received) + 1
        return self.value
