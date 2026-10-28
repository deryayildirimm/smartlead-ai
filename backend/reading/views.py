from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Genre
from .serializers import ReadingSettingsInputSerializer
from .services import get_reading_settings, save_reading_settings


class GenreListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(list(Genre.objects.filter(is_active=True).values("code", "name")))


class ReadingSettingsView(APIView):
    def get(self, request):
        return Response(get_reading_settings(request.user))

    def put(self, request):
        serializer = ReadingSettingsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(save_reading_settings(request.user, serializer.validated_data))
