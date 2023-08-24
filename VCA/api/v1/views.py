from rest_framework import viewsets, mixins

from ... import serializers, models


class AppVersionViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = serializers.AppVersionSerializer
    queryset = models.AppVersion.objects.all()
