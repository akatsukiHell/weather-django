from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SearchedCitys
from .serializers import CitySearchCountSerializer

@api_view(['GET'])
def city_search_stats(request):
    stats = (
        SearchedCitys.objects
        .values('city__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    data = [{'city': item['city__name'], 'count': item['count']} for item in stats]
    serializer = CitySearchCountSerializer(data, many=True)
    return Response(serializer.data)