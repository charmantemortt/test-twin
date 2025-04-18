from django.db import models


class CallRequest(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField()

    def __str__(self):
        return f"{self.name} {self.phone}"