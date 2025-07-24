from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .media_models import MediaImage
from .serializers import MediaImageSerializer
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import base64

class MediaImageViewSet(viewsets.ModelViewSet):
    queryset = MediaImage.objects.all()
    serializer_class = MediaImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return MediaImage.objects.all().order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        images = request.data.getlist('images', [])
        if not images:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        created_images = []
        for image_data in images:
            serializer = self.get_serializer(data={'image': image_data})
            if serializer.is_valid():
                serializer.save()
                created_images.append(serializer.data)
            else:
                # If any image fails, delete all created images
                for img in created_images:
                    MediaImage.objects.filter(id=img['id']).delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(created_images, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        media_image = get_object_or_404(MediaImage, pk=pk)
        if not media_image.image_data or not media_image.image_type:
            return Response({'error': 'Image not found'}, status=404)
            
        response = HttpResponse(media_image.image_data, content_type=f'image/{media_image.image_type}')
        response['Content-Disposition'] = f'attachment; filename="image.{media_image.image_type}"'
        return response
    
    def perform_update(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        # No need to delete files since we store data in DB
        instance.delete() 