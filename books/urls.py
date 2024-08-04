from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.SearchBooksView.as_view(), name='search_books'),
    path('create/', views.CreateBookView.as_view(), name='search_books'),
    path('recommend/', views.RecommendBookView.as_view(), name='recommend_book'),
    path('recommendations/', views.GetRecommendationsView.as_view(), name='get_recommendations'),
    path('like/<int:recommendation_id>/', views.LikeRecommendationView.as_view(), name='like_recommendation'),
]