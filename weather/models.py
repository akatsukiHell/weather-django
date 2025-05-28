from django.db import models

class City(models.Model):
    name = models.CharField(max_length=58)

    def __str__(self):
        return self.name
    

class SearchedCitys(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Аноним искал город {self.city} в {self.timestamp}"