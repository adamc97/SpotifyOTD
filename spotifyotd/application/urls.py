from django.urls import path
from .views import callback, home

urlpatterns = [
path('', home, name='home'),
path('onthisday/', callback),
]