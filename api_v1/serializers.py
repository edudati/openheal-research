from rest_framework import serializers

class CollisionSerializer(serializers.Serializer):
    timestamp = serializers.FloatField()
    barrier_id = serializers.CharField()

class TrackingItemSerializer(serializers.Serializer):
    timestamp = serializers.FloatField()
    position = serializers.ListField(child=serializers.FloatField(), min_length=3, max_length=3)
    velocity = serializers.ListField(child=serializers.FloatField(), min_length=3, max_length=3)
    direction = serializers.ListField(child=serializers.FloatField(), min_length=3, max_length=3)
    state = serializers.CharField()
    segment_id = serializers.CharField(allow_blank=True, required=False)
    gravity = serializers.FloatField(required=False)

class IngestChunkSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False, allow_null=True)

    roblox_user_id = serializers.CharField()
    roblox_user_name = serializers.CharField()

    race_start = serializers.CharField()   # ISO8601 string
    race_time = serializers.FloatField(required=False)

    collisions = CollisionSerializer(many=True, required=False)
    tracking = TrackingItemSerializer(many=True)
