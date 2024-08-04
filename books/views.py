from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Book, Recommendation, Like
from django.db.models import Count
from django.db.models import Q
from .serializers import BookSerializer, RecommendationSerializer
import requests
import os

GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY')

class CreateBookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        if 'google_books_id' not in data or not data['google_books_id']:
            data['google_books_id'] = Book.generate_google_books_id()
        
        serializer = BookSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SearchBooksView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')

        if not query:
            return Response(
                {"error": "Please provide a search query using the 'q' parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        local_books = Book.objects.filter(
            Q(title__icontains=query) | 
            Q(authors__icontains=query) | 
            Q(categories__icontains=query) |
            Q(google_books_id__icontains=query)  # Add this line to search by google_books_id
        )
        local_results = BookSerializer(local_books, many=True).data
       
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={GOOGLE_BOOKS_API_KEY}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            api_results = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                book = {
                    'google_books_id': item['id'],
                    'title': volume_info.get('title', ''),
                    'authors': ', '.join(volume_info.get('authors', [])),
                    'description': volume_info.get('description', ''),
                    'cover_image_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                    'average_rating': volume_info.get('averageRating'),
                    'categories': ', '.join(volume_info.get('categories', [])),
                    'created_by': None
                }
                api_results.append(book)

            all_results = local_results + api_results
            books = {book['google_books_id']: book for book in all_results}.values()
            
            return Response(list(books))
        except requests.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecommendBookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        google_books_id = request.data.get('google_books_id')
        comment = request.data.get('comment')

        if not google_books_id or not comment:
            return Response({'error': 'Both google_books_id and comment are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        book, created = Book.objects.get_or_create(google_books_id=google_books_id)
        
        if created:
            # Fetch book details from Google Books API
            url = f"https://www.googleapis.com/books/v1/volumes/{google_books_id}?key={GOOGLE_BOOKS_API_KEY}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                volume_info = data.get('volumeInfo', {})
                
                book.title = volume_info.get('title', '')
                book.authors = ', '.join(volume_info.get('authors', []))
                book.description = volume_info.get('description', '')
                book.cover_image_url = volume_info.get('imageLinks', {}).get('thumbnail', '')
                book.average_rating = volume_info.get('averageRating')
                book.categories = ', '.join(volume_info.get('categories', []))
                book.save()
            except requests.RequestException as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        recommendation, created = Recommendation.objects.get_or_create(
            user=request.user,
            book=book,
            defaults={'comment': comment}
        )

        if not created:
            recommendation.comment = comment
            recommendation.save()

        serializer = RecommendationSerializer(recommendation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetRecommendationsView(APIView):
    def get(self, request):
        recommendations = Recommendation.objects.all()

        # Apply filters
        genre = request.GET.get('genre')
        if genre:
            recommendations = recommendations.filter(book__categories__icontains=genre)

        min_rating = request.GET.get('min_rating')
        if min_rating:
            recommendations = recommendations.filter(book__average_rating__gte=float(min_rating))

        # Apply sorting
        sort_by = request.GET.get('sort_by', 'created_at')
        if sort_by == 'rating':
            recommendations = recommendations.order_by('-book__average_rating')
        elif sort_by == 'likes':
            recommendations = recommendations.annotate(like_count=Count('like')).order_by('-like_count')
        else:
            recommendations = recommendations.order_by('-created_at')

        serializer = RecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)

class LikeRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(Recommendation, id=recommendation_id)
        like, created = Like.objects.get_or_create(user=request.user, recommendation=recommendation)

        if not created:
            like.delete()
            return Response({'message': 'Like removed'}, status=status.HTTP_200_OK)

        return Response({'message': 'Like added'}, status=status.HTTP_201_CREATED)
