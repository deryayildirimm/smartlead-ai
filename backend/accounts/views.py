from rest_framework.response import Response
from rest_framework.views import APIView


class MeView(APIView):
    def get(self, request):
        return Response(
            {
                "id": str(request.user.pk),
                "email": request.user.email,
                "display_name": request.user.display_name,
                "email_verified": request.user.email_verified_at is not None,
            }
        )
