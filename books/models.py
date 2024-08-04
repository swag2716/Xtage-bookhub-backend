from django.db import models
from django.contrib.auth.models import User
import uuid

class Book(models.Model):
    google_books_id = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    authors = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    categories = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_books')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    @staticmethod
    def generate_google_books_id():
        return f"LOCALDB-{uuid.uuid4().hex[:12].upper()}"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s recommendation for {self.book.title}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recommendation')

    def __str__(self):
        return f"{self.user.username} likes {self.recommendation}"
