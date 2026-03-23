from django.urls import path
from django.http import HttpResponse
from . import views

def test_accounts(request):
    return HttpResponse("Accounts app is working!")

urlpatterns = [
    path('test/', test_accounts),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]