from rest_framework import serializers

from . import models


class PathImageField(serializers.ImageField):
    
    def to_representation(self, value):
        if not value:
            return None
        try:
            url = value.url
        except AttributeError:
            return None
        return url


class AppVersionSerializer(serializers.ModelSerializer):
    attachment = PathImageField()
    
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
            'deprecated_at',
        ]
