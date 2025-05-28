from django.urls import path

from . import views, api

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search_city, name="search-city"),
    path("weather/<str:city_name>", views.city_weather, name="city-weather"),
    path("api/city-stats/", api.city_search_stats, name="city-search-stats"),
]
