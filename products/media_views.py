from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .media_models import MediaImage
from .media_serializers import MediaImageSerializer
from django.http import FileResponse
from django.shortcuts import get_object_or_404
import os

class MediaImageViewSet(viewsets.ModelViewSet):
    queryset = MediaImage.objects.all()
    serializer_class = MediaImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MediaImage.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        media_image = get_object_or_404(MediaImage, pk=pk)
        file_path = media_image.image.path
        
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        return Response({'error': 'File not found'}, status=404)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        instance.delete() 