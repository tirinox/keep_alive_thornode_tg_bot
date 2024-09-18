from utils import now_ts


class Cooldown:
    def __init__(self, key, duration: float, max_duration: float = None, grow_factor: float = 2.0):
        self.key = key
        self.start_duration = duration
        self.duration = duration
        if max_duration is None:
            max_duration = duration * 10
        self.max_duration = max_duration
        self.grow_factor = grow_factor
        self.last_time = None

        assert self.duration > 0

    @property
    def ready(self):
        if self.last_time is None:
            return True
        return now_ts() - self.last_time > self.duration

    def do(self):
        self.last_time = now_ts()

    def grow_duration(self):
        self.duration = min(self.duration * self.grow_factor, self.max_duration)

    def reset_duration(self):
        self.duration = self.start_duration
