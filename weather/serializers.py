from rest_framework import serializers

class CitySearchCountSerializer(serializers.Serializer):
    city = serializers.CharField()
    count = serializers.IntegerField()