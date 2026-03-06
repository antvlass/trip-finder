from django.db import models


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=2)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        managed = False
        db_table = "airports"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Trip(models.Model):
    outbound_airport = models.CharField(max_length=3)
    inbound_airport = models.CharField(max_length=3)
    outbound_date = models.DateField()
    inbound_date = models.DateField()
    price = models.IntegerField()
    normal_price = models.IntegerField()
    discount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trips"
        ordering = ["price", "outbound_date"]
        indexes = [
            models.Index(fields=["outbound_date", "inbound_date"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.outbound_airport} → {self.inbound_airport} ({self.outbound_date} - {self.inbound_date})"

    @property
    def duration_days(self):
        return (self.inbound_date - self.outbound_date).days

    @property
    def formatted_price(self):
        return f"{self.price:,}"

    @property
    def formatted_normal_price(self):
        return f"{self.normal_price:,}"
