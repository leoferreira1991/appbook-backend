from social.models import Review, Highlight
print(f"Reviews: {Review.objects.count()}, Highlights: {Highlight.objects.count()}")
