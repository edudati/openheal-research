from django.core.management.base import BaseCommand
from research_admin.models import Participant, Study
from research_admin.services.openheal_matches import sync_matches_for_participant

class Command(BaseCommand):
    help = "Cria apenas Matches novos a partir do OpenHeal (por participante)."

    def add_arguments(self, parser):
        parser.add_argument("--participant", help="OpenHeal ID do participante (PK local).")
        parser.add_argument("--study", help="Code do estudo para limitar.")
        parser.add_argument("--dry-run", action="store_true", help="Não cria, apenas reporta.")

    def handle(self, *args, **opts):
        qs = Participant.objects.all()
        if opts.get("participant"):
            qs = qs.filter(pk=opts["participant"])
        if opts.get("study"):
            qs = qs.filter(study__code=opts["study"])

        total_new = 0
        for p in qs.iterator():
            if opts["dry_run"]:
                created = 0
            else:
                created = sync_matches_for_participant(p, default_moment_id=0)
            self.stdout.write(f"{p.id}: +{created}")
            total_new += created
        self.stdout.write(self.style.SUCCESS(f"Total criadas: {total_new}"))
