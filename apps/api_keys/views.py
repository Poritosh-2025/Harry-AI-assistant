from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsSuperAdmin, IsAdmin
from .models import APIKey, APIKeyLog
from .serializers import (
    APIKeyListSerializer, APIKeyCreateSerializer,
    APIKeyDetailSerializer, APIKeyLogSerializer
)


def api_response(status_type, message, data=None, errors=None):
    """Standard API response"""
    response = {"status": status_type, "message": message}
    if data:
        response["data"] = data
    if errors:
        response["error"] = {"code": "VALIDATION_ERROR", "details": errors}
    return response


class APIKeyListView(APIView):
    """GET /api/admin/api-keys/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        api_keys = APIKey.objects.all().order_by('-created_at')
        serializer = APIKeyListSerializer(api_keys, many=True)
        
        return Response(
            api_response("success", "API keys retrieved", {
                "api_keys": serializer.data
            })
        )


class APIKeyCreateView(APIView):
    """POST /api/admin/api-keys/create/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def post(self, request):
        serializer = APIKeyCreateSerializer(data=request.data)
        if serializer.is_valid():
            api_key = APIKey.objects.create(
                key_name=serializer.validated_data['key_name'],
                description=serializer.validated_data.get('description', ''),
                permissions=serializer.validated_data.get('permissions', ['read']),
                created_by=request.user
            )
            
            # Return full key (only shown once)
            return Response(
                api_response("success", "API key created successfully.", 
                    APIKeyDetailSerializer(api_key).data
                ),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            api_response("error", "Validation failed", errors=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class APIKeyRevokeView(APIView):
    """DELETE /api/admin/api-keys/{api_key_id}/revoke/"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def delete(self, request, api_key_id):
        try:
            api_key = APIKey.objects.get(id=api_key_id)
        except APIKey.DoesNotExist:
            return Response(
                api_response("error", "API key not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        api_key.delete()
        
        return Response(
            api_response("success", "API key revoked successfully.")
        )


class APIKeyLogsView(APIView):
    """GET /api/admin/api-keys/{api_key_id}/logs/"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request, api_key_id):
        try:
            api_key = APIKey.objects.get(id=api_key_id)
        except APIKey.DoesNotExist:
            return Response(
                api_response("error", "API key not found"),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get query params
        page = int(request.query_params.get('page', 1))
        page_size = 20
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        logs = api_key.logs.all()
        
        # Filter by date
        if date_from:
            logs = logs.filter(timestamp__date__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__date__lte=date_to)
        
        # Pagination
        total = logs.count()
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = APIKeyLogSerializer(logs[start:end], many=True)
        
        return Response(
            api_response("success", "Logs retrieved", {
                "logs": serializer.data,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "prev_page": page - 1 if page > 1 else None,
                    "next_page": page + 1 if page < total_pages else None
                }
            })
        )
