from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('form/', views.DateFormview, name='form')
    path('base/', views.base, name='base'),
    path('base/<int:farm_id>', views.farm),
    path('ndvi/<int:farm_id>', views.ndviview, name='ndvi'),
    path('weather/<int:farm_id>', views.weather, name='weather'),
    path('lulc/<int:farm_id>', views.lulc, name='lulc'),
    path('get-shapefile-midpoint/<int:farm_id>', views.get_shapefile_midpoint, name='get_shapefile_midpoint'),
]