from rest_framework import serializers

from . import models


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AppVersion
        fields = [
            'version_id',
            'version_name',
            'name',
            'added_feature',
            'details',
            'attachment',
            'base',
        ]
        
