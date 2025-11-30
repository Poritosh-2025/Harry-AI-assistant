from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import ProfileViewSerializer, ProfileUpdateSerializer


def api_response(status_type, message, data=None, errors=None):
    """Standard API response"""
    response = {"status": status_type, "message": message}
    if data:
        response["data"] = data
    if errors:
        response["error"] = {"code": "VALIDATION_ERROR", "details": errors}
    return response


class ProfileView(APIView):
    """GET /api/profile/view/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = ProfileViewSerializer(request.user)
        return Response(
            api_response("success", "Profile retrieved", serializer.data)
        )


class ProfileUpdateView(APIView):
    """PATCH /api/profile/update/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                api_response("success", "Profile updated successfully.", serializer.data)
            )
        
        return Response(
            api_response("error", "Validation failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )
