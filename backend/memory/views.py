from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MemorySerializer
from .services import MemoryService


class MemoryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: MemorySerializer(many=True)},
    )
    def get(self, request):
        memories = MemoryService.list_memories(
            user=request.user,
        )

        serializer = MemorySerializer(
            memories,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=MemorySerializer,
        responses={201: MemorySerializer},
    )
    def post(self, request):
        serializer = MemorySerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        memory = MemoryService.create_memory(
            user=request.user,
            **serializer.validated_data,
        )

        return Response(
            MemorySerializer(memory).data,
            status=status.HTTP_201_CREATED,
        )


class MemoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MemorySerializer

    def get_memory(self, request, memory_id):
        return MemoryService.get_memory(
            user=request.user,
            memory_id=memory_id,
        )

    @extend_schema(
        operation_id="memory_detail",
        responses={200: MemorySerializer},
    )
    def get(self, request, memory_id):
        memory = self.get_memory(
            request,
            memory_id,
        )

        if memory is None:
            return Response(
                {"detail": "Memory not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            MemorySerializer(memory).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="memory_update",
        request=MemorySerializer,
        responses={200: MemorySerializer},
    )
    def patch(self, request, memory_id):
        memory = self.get_memory(
            request,
            memory_id,
        )

        if memory is None:
            return Response(
                {"detail": "Memory not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MemorySerializer(
            memory,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)

        memory = MemoryService.update_memory(
            user=request.user,
            memory_id=memory_id,
            **serializer.validated_data,
        )

        return Response(
            MemorySerializer(memory).data,
            status=status.HTTP_200_OK,
        )
    
    @extend_schema(
        operation_id="memory_delete",
        responses={204: None},
    )
    def delete(self, request, memory_id):
        deleted = MemoryService.delete_memory(
            user=request.user,
            memory_id=memory_id,
        )

        if not deleted:
            return Response(
                {"detail": "Memory not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

class MemoryDeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MemorySerializer

    @extend_schema(
        operation_id="memory_deactivate",
        responses={200: MemorySerializer},
    )
    def post(self, request, memory_id):
        memory = MemoryService.get_memory(
            user=request.user,
            memory_id=memory_id,
        )

        if memory is None:
            return Response(
                {"detail": "Memory not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        memory = MemoryService.deactivate_memory(
            user=request.user,
            memory_id=memory_id,
        )

        return Response(
            MemorySerializer(memory).data,
            status=status.HTTP_200_OK,
        )    