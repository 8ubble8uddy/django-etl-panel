from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('etl/', admin.site.urls),
]
