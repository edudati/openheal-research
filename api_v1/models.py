# api_v1/models.py
from django.db import models

class IngestChunk(models.Model):
    # ligação opcional com usuário interno da sua base (pode ser preenchido depois)
    user_id = models.IntegerField(null=True, blank=True)

    # dados vindos do roblox
    roblox_user_id = models.CharField(max_length=255)
    roblox_user_name = models.CharField(max_length=255)

    race_start = models.DateTimeField()
    race_time = models.FloatField(null=True, blank=True)

    collisions = models.JSONField(default=list, blank=True)
    tracking = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IngestChunk {self.roblox_user_name} ({self.roblox_user_id})"
