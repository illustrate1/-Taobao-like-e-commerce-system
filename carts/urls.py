from django.urls import path
from . import views

urlpatterns = [
    path("<str:uername>", views.CartsView.as_view())
]