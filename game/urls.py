from django.urls import path
from . import views

urlpatterns = [
    # ১. মেইন মেনু বা হোম পেজ (যেখানে Single/Double মোড সিলেক্ট করবে)
    path('', views.index, name='index'), 

    # ২. গেম খেলার পেজ (রুম কোড অনুযায়ী)
    path('game/<str:room_code>/', views.tic_tac_toe_online, name='game'),
]