from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('form/', views.DateFormview, name='form')
    path('base/', views.base, name='base'),
    path('base/<int:farm_id>', views.farm),
]