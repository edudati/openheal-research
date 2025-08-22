from django.db import connections, transaction
from datetime import datetime
from ..models import Match

SQL_MATCHES = '''
  SELECT m."Id", m."PresetId", m."LevelId", m."ResultId", m."Date", sr."ScreenResolution" AS "ScreenSize"
  FROM "Matches" m
  LEFT JOIN (
    SELECT "MatchId", MAX("ScreenResolution") AS "ScreenResolution"
    FROM "BubblesData"
    GROUP BY "MatchId"
  ) sr ON sr."MatchId" = m."Id"
  WHERE m."UserDataId" = %s
  ORDER BY m."Date" ASC
'''

def fetch_matches_external(user_data_id: int) -> list[dict]:
    with connections["openheal_ext"].cursor() as cur:
        cur.execute(SQL_MATCHES, [user_data_id])
        rows = cur.fetchall()
    out = []
    for m_id, preset, level, result, dt, screen in rows:
        if isinstance(dt, str):
            try: dt = datetime.fromisoformat(dt.replace(" ", "T"))
            except Exception: pass
        out.append({
            "id": str(m_id),
            "preset_id": int(preset) if preset is not None else 0,
            "level_id": int(level) if level is not None else None,
            "result_id": str(result) if result is not None else "",
            "date": dt,
            "screen_size": (str(screen) if screen is not None else None),
        })
    return out

def sync_matches_for_participant(participant) -> int:
    user_data_id = int(participant.id)
    ext = fetch_matches_external(user_data_id)
    created_count = 0
    with transaction.atomic(using="default"):
        for m in ext:
            _, created = Match.objects.using("default").get_or_create(
                id=m["id"],
                defaults={
                    "participant": participant,
                    "preset_id": m["preset_id"],
                    "level_id": m["level_id"],
                    "phase_id": None,
                    "intervention_id": None,
                    "moment_id": None,
                    "result_id": m["result_id"],
                    "date": m["date"],
                    "screen_size": m["screen_size"],
                    "is_active": True,
                    "is_used": True,
                },
            )
            if created:
                created_count += 1
    return created_count
