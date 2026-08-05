from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_document, name="upload"),
    path("documents/<int:pk>/", views.review_document, name="review"),
    path("documents/<int:pk>/preview/", views.preview_document, name="preview"),
    path("documents/<int:pk>/reanalyze/", views.reanalyze_document, name="reanalyze"),
    path("documents/<int:pk>/files/<str:field_name>/", views.document_file, name="file"),
]
