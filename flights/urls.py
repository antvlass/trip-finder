from django.urls import path

from . import views

app_name = "flights"

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search_flights, name="search"),
]
