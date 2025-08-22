# api_v1/views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .serializers import IngestChunkSerializer
from .models import IngestChunk

@extend_schema(
    tags=['Roblox'],
    summary='Ingest Roblox Race Data',
    description='Recebe dados de corridas do Roblox incluindo tracking, colisões e métricas de performance',
    request=IngestChunkSerializer,
    responses={
        200: {
            'description': 'Dados recebidos com sucesso',
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'id': {'type': 'integer', 'example': 1},
                'received': {'type': 'integer', 'example': 0}
            }
        },
        400: {
            'description': 'Dados inválidos',
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'invalid'},
                'errors': {'type': 'object'}
            }
        },
        401: {
            'description': 'API Key inválida',
            'type': 'object',
            'properties': {
                'detail': {'type': 'string', 'example': 'unauthorised'}
            }
        }
    },
    examples=[
        OpenApiExample(
            'Exemplo Básico',
            value={
                "roblox_user_id": "test123",
                "roblox_user_name": "TestUser",
                "race_start": "2024-08-22T10:30:00Z",
                "tracking": []
            }
        ),
        OpenApiExample(
            'Exemplo Completo',
            value={
                "user_id": 1001,
                "roblox_user_id": "roblox_player_789",
                "roblox_user_name": "SpeedRunner2024",
                "race_start": "2024-08-22T10:30:00Z",
                "race_time": 67.45,
                "collisions": [
                    {
                        "timestamp": 12.3,
                        "barrier_id": "wall_north_01"
                    }
                ],
                "tracking": [
                    {
                        "timestamp": 0.0,
                        "position": [0, 0, 0],
                        "velocity": [0, 0, 0],
                        "direction": [1, 0, 0],
                        "state": "starting"
                    }
                ]
            }
        )
    ],
    parameters=[
        OpenApiParameter(
            name='X-API-Key',
            location=OpenApiParameter.HEADER,
            description='API Key para autenticação',
            required=True,
            type=str
        )
    ]
)
@api_view(["POST"])
@authentication_classes([])              # sem sessão/CSRF
@permission_classes([AllowAny])
def roblox_ingest(request):
    # API key simples (header: X-API-Key)
    api_key = request.headers.get("X-API-Key")
    if getattr(settings, "API_INGEST_KEY", None) and api_key != settings.API_INGEST_KEY:
        return Response({"detail": "unauthorised"}, status=401)

    ser = IngestChunkSerializer(data=request.data)
    if not ser.is_valid():
        return Response({"status": "invalid", "errors": ser.errors}, status=400)

    data = ser.validated_data

    # parse do timestamp ISO8601
    dt = parse_datetime(data["race_start"])
    if not dt:
        return Response({"status": "invalid", "errors": {"race_start": ["Invalid ISO8601 datetime"]}}, status=400)

    obj = IngestChunk.objects.create(
        user_id=data.get("user_id"),  # pode ser None
        roblox_user_id=data["roblox_user_id"],
        roblox_user_name=data["roblox_user_name"],
        race_start=dt,
        race_time=data.get("race_time", 0.0),
        collisions=data.get("collisions", []),
        tracking=data["tracking"],
    )

    return Response({"status": "ok", "id": obj.id, "received": len(obj.tracking)})
