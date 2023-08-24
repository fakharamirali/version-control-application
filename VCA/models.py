import re

from django.contrib import admin
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.db.models import QuerySet
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from .deletion import restrict_or_upgrade
from .validators import path_validators, view_path_validators

__all__ = [
    'BaseVersion',
    'WebVersion',
    'AppVersion',
    'WebAPI',
    'WebAPIRequiredByApp',
    'main_models',
]

main_version = re.compile(r'\d+\.0\.0')
sub_version = re.compile(r'\d+\.\d+\.0')
tiny_version = re.compile(r'\d+\.\d+\.\d+')


def _append_slash(url: str) -> str:
    return url + ('' if url.endswith('/') else '/')


class DepreciableObjectMixin(models.Model):
    class Meta:
        abstract = True
    
    deprecated_at = models.DateTimeField(_('Deprecate Date'), null=True, blank=True)
    
    @property
    def _is_deprecated_time(self) -> bool:
        return self.deprecated_at is not None and now() > self.deprecated_at
    
    # can override in children
    def deprecated(self) -> bool:
        return self._is_deprecated_time
    
    def get_deprecated_time(self):
        return self.deprecated_at
    
    @admin.display(description=_("Deprecate Date"))
    def show_deprecated_time(self):
        return self.get_deprecated_time()
    
    @admin.display(boolean=True, description=_("Deprecated"))
    def show_deprecated(self):
        return self.deprecated()
    
    @staticmethod
    @admin.action(permissions=['change'], description=_("Deprecate"))
    def deprecate(modeladmin, request, queryset: 'QuerySet[DepreciableObjectMixin]'):
        for obj in queryset:
            if not obj._is_deprecated_time:
                obj.deprecated_at = now()
                obj.save()
    
    @staticmethod
    @admin.action(permissions=['change'], description=_("Republish"))
    def republish(modeladmin, request, queryset: 'QuerySet[DepreciableObjectMixin]'):
        queryset.update(deprecated_at=None)


class BaseVersion(DepreciableObjectMixin, models.Model):
    class Meta:
        db_tablespace = "version"
        abstract = True
        ordering = ('version_id',)
    
    version_id = models.PositiveSmallIntegerField(_("Version Id"), primary_key=True)
    version_name = models.CharField(_("Version Name"), max_length=255, unique=True, null=False,
                                    validators=(RegexValidator(r'\d+\.\d+\.\d+'),))
    name = models.CharField(_("Name"), max_length=255)
    added_feature = models.TextField(_("Added Features"))
    details = models.TextField(_("Details"))
    
    def __str__(self):
        return "V" + self.version_name


class GraphAsyncVersion(DepreciableObjectMixin, models.Model):
    class Meta:
        abstract = True
    
    # Just skin-deep save
    # Use symmetrical=False to difference between source and target
    previous_versions = models.ManyToManyField('self', symmetrical=False, related_name='next_versions',
                                               verbose_name=_("Previous Versions"), blank=True,
                                               )
    # Just skin-deep save
    # Use symmetrical=False to difference between source and target
    incompatible_previous_versions = models.ManyToManyField('self', symmetrical=False, blank=True,
                                                            related_name='incompatible_next_versions',
                                                            verbose_name=_("Incompatible Previous version"),
                                                            )
    
    # Deep Check Recursive
    def all_previous_version(self) -> 'list[GraphAsyncVersion]':
        previous_versions = []
        for version in self.get_previous_versions():
            previous_versions.append(version)
            previous_versions.extend(version.all_previous_version())
        return previous_versions
    
    # Deep Check Recursive
    def all_next_version(self) -> 'list[GraphAsyncVersion]':
        next_versions = []
        for version in self.next_versions.all():
            next_versions.append(version)
            next_versions.extend(version.all_next_version())
        return next_versions
    
    def deprecated(self) -> bool:
        return super().deprecated() and not self.coming_soon()
    
    def available(self) -> bool:
        if self.deprecated() or self.coming_soon():
            return False
        for version in self.get_incompatible_previous_versions():
            if not version.deprecated_show or version.available() or version.coming_soon():
                return False
        return True
    
    def get_incompatible_previous_versions(self):
        return self.incompatible_previous_versions.all()
    
    def coming_soon(self) -> bool:
        # Check previous version is published
        for previous_version in self.get_previous_versions():
            if previous_version.coming_soon():
                return True
        
        # Check incompatible version is deprecated
        for previous_version in self.get_incompatible_previous_versions():
            if not previous_version.deprecated():
                return True
        return False
    
    def get_previous_versions(self) -> 'QuerySet[GraphAsyncVersion]':
        return self.previous_versions.all()
    
    @admin.display(boolean=True, description=_("Coming Soon"))
    def show_coming_soon(self) -> bool:
        return self.coming_soon()


class AppVersion(BaseVersion):
    class Meta:
        db_tablespace = "version"
        verbose_name = _("Application Version")
        verbose_name_plural = _("Application Versions")
        ordering = ('version_id',)
    
    attachment = models.FileField(_("Application File"), upload_to="apk", validators=(FileExtensionValidator(['apk']),))
    base_dependency_web_version = models.ForeignKey("WebVersion", models.RESTRICT, related_name="base_depended_by",
                                                    null=True, blank=True)
    base = models.ForeignKey('self', models.SET_NULL, related_name="developed_versions", verbose_name=_("Base"),
                             null=True, blank=True,
                             limit_choices_to={'version_id__lt': models.F('version_id')})
    
    web_apis_required = models.ManyToManyField('WebAPI', related_name='app_versions_using',
                                               through='WebAPIRequiredByApp', through_fields=('app_version', 'web_api'))
    
    def deprecated(self) -> bool:
        return super().deprecated() or not self.supported()
    
    def supported(self) -> bool:
        for web_api in self.web_apis_required.all():
            if web_api.available:
                return True
        
        return True


class WebVersion(GraphAsyncVersion, BaseVersion):
    class Meta:
        db_tablespace = 'version'
        ordering = ('version_id',)
        verbose_name = _("Website Version")
        verbose_name_plural = _("Website Versions")
    
    weblog_url = models.CharField(_("Weblog Address"), validators=path_validators, null=True, blank=True,
                                  max_length=128)
    panel_url = models.CharField(_("Panel Address"), validators=path_validators, null=True, blank=True,
                                 max_length=128)
    login_url = models.CharField(_("Login Address"), validators=path_validators, null=True, blank=True,
                                 max_length=128)
    register_url = models.CharField(_("Register Address"), validators=path_validators, null=True, blank=True,
                                    max_length=128)
    api_prefix = models.CharField(_("API Prefix"), validators=view_path_validators, null=True, blank=True,
                                  max_length=128)
    
    def get_complete_prefix(self, is_api=True):
        if is_api:
            if self.api_prefix is None:
                return
            return _append_slash(self.api_prefix) + _append_slash(self.get_version_uri())
        return _append_slash(self.get_version_uri())
    
    def get_version_uri(self):
        if main_version.match(self.version_name):
            return 'v' + self.version_name.partition('.')[0]
        elif sub_version.match(self.version_name):
            return 'v' + self.version_name.rpartition('.')[-1]
        elif tiny_version.match(self.version_name):
            return 'v' + self.version_name
        else:
            return 'v' + self.version_name


class WebAPI(DepreciableObjectMixin, models.Model):
    class Meta:
        db_tablespace = 'version'
        verbose_name = _("Website View Version")
        verbose_name_plural = _("Website View Versions")
    
    web_version = models.ForeignKey('WebVersion', models.PROTECT, related_name='views',
                                    verbose_name=_("Website Version"))
    view_code_name = models.SlugField(_("View Code"), unique=True)
    view_name = models.CharField(_("View Name"), max_length=128, null=True, blank=True)
    view_url = models.CharField(_("View Url"), max_length=255, validators=view_path_validators, null=True, blank=True)
    absolute_view_url = models.CharField(_("Absolute View Url"), max_length=255, validators=view_path_validators,
                                         null=True,
                                         blank=True)
    is_api = models.BooleanField(_("Is API"), default=False)
    new_compatible_view = models.ForeignKey('self', models.SET_NULL, related_name='supported_views',
                                            verbose_name=_("Update"), null=True, blank=True)
    
    @property
    def available(self):
        return not self.deprecated and self.web_version.available() and not self.coming_soon()
    
    @property
    def url(self):
        if self.absolute_view_url is not None:
            return self.absolute_view_url
        elif self.view_url is not None:
            return self.web_version.get_complete_prefix(self.is_api) + self.view_url
        else:
            return None
    
    def updates(self):
        if self.new_compatible_view is not None:
            return [self.new_compatible_view] + self.new_compatible_view.updates()
        return []
    
    def last_update(self):
        updates = self.updates()
        if updates:
            return updates[-1]
    
    def available_updates(self):
        if self.new_compatible_view is not None and self.new_compatible_view.web_version.available():
            return [self.new_compatible_view] + self.new_compatible_view.updates()
        return []
    
    def clean(self):
        if self.absolute_view_url.startswith(self.web_version.get_complete_prefix(is_api=self.is_api)):
            if self.view_url is None:
                self.view_url = self.absolute_view_url.removeprefix(
                    self.web_version.get_complete_prefix(is_api=self.is_api))
    
    def last_available_update(self):
        if not self.available:
            return
        update = self
        while update.new_compatible_view.available:
            update = update.new_compatible_view
        return update
    
    def coming_soon(self):
        return self.web_version.coming_soon()
    
    def __str__(self):
        if self.view_name is not None:
            return f"{self.view_name} (V{self.web_version.version_name})"


class WebAPIRequiredByApp(models.Model):
    class Meta:
        db_tablespace = 'version'
        verbose_name = _("Dependency")
        verbose_name_plural = _("Dependencies")
    
    app_version = models.ForeignKey('AppVersion', models.CASCADE)
    web_api = models.ForeignKey('WebAPI', restrict_or_upgrade)


main_models = [
    AppVersion,
    WebVersion,
    WebAPI,
    WebAPIRequiredByApp,
]
