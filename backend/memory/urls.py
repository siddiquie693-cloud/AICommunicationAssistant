from django.urls import path

from .views import (
    MemoryDetailAPIView,
    MemoryDeactivateAPIView,
    MemoryListCreateAPIView,
)


urlpatterns = [
    path(
        "",
        MemoryListCreateAPIView.as_view(),
        name="memory-list-create",
    ),
    path(
        "<int:memory_id>/",
        MemoryDetailAPIView.as_view(),
        name="memory-detail",
    ),
    path(
        "<int:memory_id>/deactivate/",
        MemoryDeactivateAPIView.as_view(),
        name="memory-deactivate",
    ),
]