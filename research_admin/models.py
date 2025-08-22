from django.db import models
from django.contrib.auth.models import User

class Study(models.Model):
    code = models.SlugField(unique=True, max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} — {self.title}"

class Researcher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=200, blank=True)
    studies = models.ManyToManyField(Study, blank=True, related_name="researchers")

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Participant(models.Model):
    GROUP_CHOICES = [("control", "Control"), ("experimental", "Experimental")]

    id = models.CharField(primary_key=True, max_length=36)  # openheal_id
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=150)
    email = models.EmailField()
    group = models.CharField(max_length=20, choices=GROUP_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.group})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["study", "email"], name="uniq_participant_email_per_study")
        ]
        indexes = [models.Index(fields=["study", "email"])]

class Match(models.Model):
    id = models.CharField(primary_key=True, max_length=36)  # ID externo
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="matches")
    preset_id = models.IntegerField()
    level_id = models.IntegerField(null=True, blank=True)
    phase_id = models.IntegerField(null=True, blank=True)
    intervention_id = models.IntegerField(null=True, blank=True)
    moment_id = models.IntegerField(null=True, blank=True)
    result_id = models.CharField(max_length=100)
    screen_size = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_used = models.BooleanField(default=True)

    def __str__(self):
        return f"Match {self.id} ({self.participant.id})"

    class Meta:
        indexes = [
            models.Index(fields=["participant", "date"]),
            models.Index(fields=["is_active", "is_used"]),
        ]

    EXTERNAL_FIELDS = ("id", "participant", "preset_id", "level_id", "result_id", "date", "screen_size")

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                orig = Match.objects.get(pk=self.pk)
                for f in self.EXTERNAL_FIELDS:
                    setattr(self, f, getattr(orig, f))
            except Match.DoesNotExist:
                pass
        super().save(*args, **kwargs)

class Ball(models.Model):
    id = models.CharField(primary_key=True, max_length=36)      # bd."Id" (BallDataId, externo)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="balls")  # bub."MatchId"

    direction = models.IntegerField(null=True, blank=True)      # bd."Direction"
    destroy_time = models.DateTimeField(null=True, blank=True)  # bd."DestroyTime"
    launch_time = models.DateTimeField(null=True, blank=True)   # bd."LaunchTime"
    hit_time = models.DateTimeField(null=True, blank=True)      # bd."HitTime"
    mature_time = models.DateTimeField(null=True, blank=True)   # bd."MatureTime"

    size = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)   # bd."Size"
    speed = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)  # bd."Speed"

    launch_coord_x = models.FloatField(null=True, blank=True)   # lcd."LaunchCoord_x"
    launch_coord_y = models.FloatField(null=True, blank=True)   # lcd."LaunchCoord_y"
    hit_coord_x = models.FloatField(null=True, blank=True)      # hcd."HitCoord_x"
    hit_coord_y = models.FloatField(null=True, blank=True)      # hcd."HitCoord_y"

    class Meta:
        indexes = [models.Index(fields=["match", "launch_time"])]

