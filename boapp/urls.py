from django.urls import path

from boapp.views import setting

app_name = 'boapp'

urlpatterns = [
    path('setting/<id>', setting, name='setting')
]
