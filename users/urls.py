# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# ⚠️ Imports locaux UNIQUEMENT ici — pas d'imports depuis d'autres apps
from users.views import (
    RegisterView,
    ChangePasswordView,
    UserViewSet,
    ResearcherViewSet,
    AdminViewSet,
    LabManagerViewSet,
    TeamLeaderViewSet,
)

router = DefaultRouter()
router.register(r'users',        UserViewSet,       basename='user')
router.register(r'researchers',  ResearcherViewSet, basename='researcher')
router.register(r'admins',       AdminViewSet,      basename='admin')
router.register(r'lab-managers', LabManagerViewSet, basename='lab-manager')
router.register(r'team-leaders', TeamLeaderViewSet, basename='team-leader')

urlpatterns = [
    path('', include(router.urls)),
    path('register/',        RegisterView.as_view(),        name='register'),
    path('login/',           TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/',   TokenRefreshView.as_view(),    name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(),  name='change_password'),
]