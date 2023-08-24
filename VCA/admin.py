from django.contrib import admin
from django.db.models import QuerySet, Q
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from . import models


# Control Registration

class FilterByDeprecated(admin.SimpleListFilter):
    title = _("Is Deprecated")
    parameter_name = 'deprecated'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', _("Yes")),
            ('no', _("No")),
        )

    def queryset(self, request, queryset: 'QuerySet[models.DepreciableObjectMixin]'):
        value = self.value()
        if value == 'yes':
            return queryset.filter(deprecated_at__lt=now())
        elif value == 'no':
            return queryset.filter(Q(deprecated_at__isnull=True) | Q(deprecated_at__gt=now()))
        else:
            return queryset


@admin.register(models.WebVersion)
class WebVersionAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('admin/VCA/web_version_details.css',),
        }
    
    list_display = [
        'version_id',
        'version_name',
        'name',
        'show_deprecated_time',
        'show_deprecated',
        'show_coming_soon',
    ]
    list_filter = [
        FilterByDeprecated
    ]
    ordering = ('version_id',)
    sortable_by = ('version_id', 'version_name')
    search_fields = ('version_name', 'name', 'added_feature')
    add_fieldsets = (
        (None, {'fields': ('version_id', 'version_name', 'name')}),
        (_("Details"), {"fields": ('added_feature', 'details')}),
    )
    fieldsets = (
        (None, {'fields': ('version_id', 'version_name', 'name')}),
        (_("Important URLs"), {
            'classes': ('url_input',),
            'fields': (
                'weblog_url',
                'panel_url',
                'login_url',
                'register_url',
                'api_prefix',
            )
        }),
        (_("Control Publish"), {'fields': (
            'previous_versions',
            'incompatible_previous_versions',
        )}),
        (_("Details"), {"fields": ('added_feature', 'details')}),
        (_("Other"), {'fields': ('deprecated_at',)}),
    )
    filter_horizontal = (
        'previous_versions',
        'incompatible_previous_versions',
    )
    actions = (
        models.DepreciableObjectMixin.deprecate,
        models.DepreciableObjectMixin.republish,
    )
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        print(locals())
        if db_field.name in ('previous_versions', 'incompatible_previous_versions'):
            kwargs["queryset"] = models.WebVersion.objects.filter(
                version_id__lt=request.resolver_match.kwargs['object_id'])
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


class WebAPIRequiredByAppInline(admin.TabularInline):
    model = models.WebAPIRequiredByApp
    extra = 1
    fieldsets = (
        (None, {"fields": ('web_api',)}),
    )


@admin.register(models.AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ['version_id', 'version_name', 'name', 'show_deprecated_time', 'show_deprecated']
    ordering = ('version_id',)
    sortable_by = ('version_id', 'version_name')
    search_fields = ('version_name', 'name', 'added_feature')
    
    add_fieldsets = (
        (None, {'fields': ('version_id', 'version_name', 'name')}),
        (_("Details"), {"fields": ('added_feature', 'details')}),
        (_("Application File"), {"fields": ('attachment',)})
    )
    fieldsets = (
        (None, {'fields': ('version_id', 'version_name', 'name')}),
        (_("Details"), {"fields": ('added_feature', 'details')}),
        (_("Other"), {'fields': ('deprecated_at',)}),
        (_("Dependency"), {"fields": (
            'base',
            'base_dependency_web_version',
        )}),
    )
    inlines = [WebAPIRequiredByAppInline]
    actions = [
        models.DepreciableObjectMixin.deprecate,
        models.DepreciableObjectMixin.republish,
    ]
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


@admin.register(models.WebAPI)
class WebAPIAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'is_api',
        'show_deprecated',
        'show_deprecated_time',
    ]
