from rest_framework import serializers
from .models import Book, Recommendation, Like
from auth_app.serializers import UserSerializer

class BookSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Book
        fields = '__all__'

class RecommendationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = '__all__'

    def get_likes_count(self, obj):
        return obj.like_set.count()