"""
URL configuration for Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/journals/', include('journal.urls')),
    path('api/keywords/', include('keywords.urls')),
    path('api/publications/', include('publication.urls')),
    path('api/citations/', include('citation.urls')),
    path('api/coauthors/', include('coAuthor.urls')),
    path('api/laboratories/', include('laboratory.urls')),
    path('api/institutions/', include('institution.urls')),
    path('api/teams/', include('team.urls')),
    path('api/users/', include('users.urls')),
    path('api/pipeline/', include('data_pipeline.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    
]
