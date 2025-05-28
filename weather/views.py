from typing import Optional

import requests
import requests_cache
from retry_requests import retry
import openmeteo_requests
import pandas as pd

import pytz
from urllib.parse import quote, unquote

from django.shortcuts import render, redirect
from django.shortcuts import render
from django.utils import timezone

from .forms import CityForm
from .models import City, SearchedCitys


# Получаем координаты и часовой пояс введённого пользователем города через API
def get_city_coordinats(city: str) -> Optional[dict]:
    url = "https://geocoding-api.open-meteo.com/v1/search?name={}&count=1&language=ru&format=json".format(city)
    city_info = requests.get(url).json()
    if not city_info.get("results"):
        return None
    return city_info["results"][0]

# Получение данных о погоде
def get_weather(params: dict) -> dict:

    # Кэшируем сессию для запросов
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Отправляем API запрос
    url = "https://api.open-meteo.com/v1/forecast"
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Получаем текущую температуру
    current = response.Current()
    current_temperature = int(current.Variables(0).Value())

    # Получаем информацию о погоде на ближайшие 2 дня с учётом локального времени
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_data = {
        "date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left").tz_convert(params["timezone"]),
        "temperature_2m": hourly_temperature_2m.astype(int)
    }
    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Получаем время по UTC и переводим его в текущее локальное время
    current_time = pd.to_datetime(current.Time(), unit='s', utc=True).tz_convert(params["timezone"])
    next_hour = current_time.floor("h") + pd.Timedelta(hours=1)
    filtered_data = hourly_dataframe[hourly_dataframe["date"] >= next_hour] # >>> фильтруем данные, чтобы получить информацию о следующем времени

    context = {
        'current_temperature': current_temperature, # >>> текущая температура
        'current_time': current_time, # >>> текущее время в формате Час:Минуты
        'hourly_temperature': filtered_data # >>> почасовая температура начиная со следующего часа
    }

    return context

# Ищем нужный город
def search_city(request):
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name']
            city_data = get_city_coordinats(city_name)

            if city_data:
                city_object, created = City.objects.get_or_create(name=city_data["name"])
                response = redirect('city-weather', city_name=city_data["name"])

                # Сохраняем историю поиска для API
                session_key = request.session.session_key
                SearchedCitys.objects.create(session_key=session_key, city=city_object)
                
                # Кодируем и сохраняем последний запрос пользователя в куки
                encoded_city = quote(city_data["name"])
                response.set_cookie('last_searched_city', encoded_city, max_age=60*60*24*7)
                return response
    else:
        form = CityForm()

    return render(request, 'weather/index.html', {'form': form})

# Получаем погоду в городе
def city_weather(request, city_name):
    city_data = get_city_coordinats(city_name)

    if not city_data:
        return redirect('index')

    params = {
        "latitude": city_data["latitude"],
        "longitude": city_data["longitude"],
        "hourly": "temperature_2m",
        "current": "temperature_2m",
        "timezone": city_data["timezone"],
        "forecast_days": 2,
        "timeformat": "unixtime",
    }

    temp_info = get_weather(params)
    current_time = temp_info["current_time"]
    current_temperature = temp_info['current_temperature']
    hour_temp = temp_info['hourly_temperature'].head(8).to_dict(orient='records') # >>> берём первые 5 следующих часов

    # Устанавливаем отображение времени с учётом часового пояса пользователя
    tz = pytz.timezone(city_data["timezone"])
    timezone.activate(tz)
    
    context = {
        'city': city_data,
        'current_temperature': current_temperature,
        'current_time': current_time,
        'hour_temp': hour_temp
    }

    return render(request, 'weather/city_weather.html', context)

# Шаблон отображения главной страницы
def index(request):
    encoded_last_city = request.COOKIES.get('last_searched_city', None)
    last_city = unquote(encoded_last_city) if encoded_last_city else None
    return render(request, 'weather/index.html', context={'form': CityForm(), 'last_city': last_city})

