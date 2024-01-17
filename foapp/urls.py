from django.urls import path

from foapp.views import search, request, find_req, accept_req

app_name = 'foapp'
urlpatterns = [
    path('search', search, name='search'),
    path('request', request, name='request'),
    path('find_req', find_req, name='find_req'),
    path('accept_req', accept_req, name='accept_req')
]
