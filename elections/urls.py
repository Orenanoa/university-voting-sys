from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .pages import PAGES

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.LoginPage.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('results/', views.results, name='results'),

    # Extra buttons
    path('election/<int:pk>/start/', views.election_start, name='election_start'),
    path('election/<int:pk>/end/', views.election_end, name='election_end'),
    path('election/<int:pk>/candidates/', views.election_candidates, name='election_candidates'),
    path('position/<int:pk>/candidates/', views.position_candidates, name='position_candidates'),
    path('candidate/<int:pk>/info/', views.candidate_info, name='candidate_info'),
]

# CRUD pages: list + create, edit, delete for each object in PAGES
for name in PAGES:
    urlpatterns += [
        path(f'{name}/', views.object_list, {'name': name}, name=name),
        path(f'{name}/<int:pk>/edit/', views.object_edit, {'name': name}, name=f'{name}_edit'),
        path(f'{name}/<int:pk>/delete/', views.object_delete, {'name': name}, name=f'{name}_delete'),
    ]
