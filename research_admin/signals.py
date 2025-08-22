from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Participant
from .services.openheal_matches import sync_matches_for_participant

@receiver(post_save, sender=Participant)
def auto_sync_matches_on_participant_create(sender, instance: Participant, created, **kwargs):
    if created:
        sync_matches_for_participant(instance)
