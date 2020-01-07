from django.urls import path
from . import views


urlpatterns = [
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('load/', views.candidates_load, name='voting'),

    path('edit/', views.voting_edit, name='voting')
]
