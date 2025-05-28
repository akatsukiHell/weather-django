from django.test import TestCase, Client
from django.urls import reverse
from django.urls import reverse

from unittest.mock import patch

from .models import City, SearchedCitys
from .forms import CityForm

class WeatherAppTests(TestCase):

    # Создаём пользователя и объект города
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(name="Москва")

    # Тест главной страницы
    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/index.html')

    # Тест формы объекта города с валидными данными
    def test_city_form_valid(self):
        form = CityForm(data={'name': 'Москва'})
        self.assertTrue(form.is_valid())

    # Тест формы объекта города с невалидными данными
    def test_city_form_invalid(self):
        form = CityForm(data={'name': ''})
        self.assertFalse(form.is_valid())

    # Тест поиска города с последующим редеректом
    def test_search_city_post_valid(self):
        response = self.client.post(reverse('search-city'), {'name': 'Москва'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(City.objects.filter(name='Москва').exists())

    # Тест редиректа на страницу с городом
    def test_search_city_creates_history(self):
        self.client.get(reverse('index'))
        self.client.post(reverse('search-city'), {'name': 'Москва'})
        self.assertTrue(SearchedCitys.objects.filter(city__name='Москва').exists())

    # Тест страницы с информацией о погоде в нужном городе
    def test_city_weather_page(self):
        response = self.client.get(reverse('city-weather', args=['Москва']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/city_weather.html')

    # Тест сохранения информации о последнем найденом городе в куки-файлах
    def test_last_searched_cookie(self):
        response = self.client.post(reverse('search-city'), {'name': 'Москва'})
        self.assertTrue(response.cookies.get('last_searched_city'))

    # Тест API для вывода городов и количества их поиска
    def test_city_stats_api(self):
        SearchedCitys.objects.create(city=self.city)
        url = reverse('city-search-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item['city'] == 'Москва' for item in data))

    
    # Мок-тест для передачи контекста в функцию с получением координат
    @patch('weather.views.get_city_coordinats')
    def test_search_city_mock_api(self, mock_get_coords):
        mock_get_coords.return_value = {
            "name": "Москва",
            "latitude": 55.75,
            "longitude": 37.62,
            "timezone": "Europe/Moscow"
        }

        response = self.client.post(reverse('search-city'), {'name': 'Москва'})
        self.assertEqual(response.status_code, 302)