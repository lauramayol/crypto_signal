"""crypto_signal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from crypto_track import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('load/nomics', views.load_nomics, name='load_nomics'),
    path('load/kaggle', views.load_kaggle, name='load_kaggle'),
    path('load/ccxt', views.load_ccxt, name='load_ccxt'),
    path('load/trends', views.load_trends, name='load_trends'),
]
