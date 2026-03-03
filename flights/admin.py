from django.contrib import admin

from .models import Airport, Trip


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country_code", "latitude", "longitude")
    search_fields = ("code", "name", "country_code")
    list_filter = ("country_code",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = (
        "outbound_airport",
        "inbound_airport",
        "outbound_date",
        "inbound_date",
        "price",
        "discount",
        "created_at",
    )
    search_fields = ("outbound_airport", "inbound_airport")
    list_filter = ("outbound_date", "inbound_date", "created_at")
    date_hierarchy = "outbound_date"
    ordering = ("price", "outbound_date")
