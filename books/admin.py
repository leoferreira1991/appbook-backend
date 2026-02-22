from django.contrib import admin
from .models import Author, Series, Book, ReadingProgress

admin.site.register(Author)
admin.site.register(Series)
admin.site.register(Book)
admin.site.register(ReadingProgress)
