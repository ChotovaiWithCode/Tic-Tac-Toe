from django.db import models

class GameRoom(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    board = models.JSONField(default=list)  # [None, None, ...]
    turn = models.CharField(max_length=1, default='X')
    next_starter = models.CharField(max_length=1, default='X')
    winner = models.CharField(max_length=1, null=True, blank=True)
    winning_line = models.CharField(max_length=20, null=True, blank=True)
    is_over = models.BooleanField(default=False)

    x_history = models.JSONField(default=list)
    o_history = models.JSONField(default=list)

    def save(self, *args, **kwargs):
        if not self.board:
            self.board = [None] * 9
        super().save(*args, **kwargs)