from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import *


urlpatterns = [
    # URL pattern for create new user
    path('create', CustomUserCreateView.as_view(), name='user-create'),

    # URL pattern for user login
    path('login', UserLoginView.as_view(), name='user-login'),

    # URL pattern for retrieving user profile
    path('profile', UserProfilesView.as_view(), name='user-profile'),

    # URL pattern for user logout
    path('logout', UserLogoutView.as_view(), name='user-logout'),

    # URL pattern for listing groups
    path('gorups', GroupsListViews.as_view(), name='group-list'),

    # URL pattern for user details
    path('detail', UserDetailsView.as_view(), name='user-detail'),
]
