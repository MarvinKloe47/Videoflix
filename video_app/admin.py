
from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
	list_display = ("title", "genre", "visibility", "processing_status", "created_at")
	list_filter = ("visibility", "genre", "processing_status")
	search_fields = ("title", "description")
