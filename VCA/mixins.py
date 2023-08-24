import warnings

from django.http import Http404, HttpResponseGone, HttpResponse, HttpResponsePermanentRedirect
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import docs
from .exceptions import NotRegisteredWarning
from .models import *


class VersionControlMixin:
    view_code = None
    view_name = None
    require_register = False
    _is_api = None
    
    register_help_text = docs.register_help_text
    
    @property
    def is_api(self):
        if self._is_api is not None:
            return self._is_api
        else:
            if issubclass(self.__class__, APIView):
                return True
            else:
                return False
    
    def dispatch(self, request, *args, **kwargs):
        if not self.available():
            res = self.control_version()
            if res is not None:
                return res
        return super().dispatch(request, *args, **kwargs)
    
    @property
    def web_api(self):
        if not hasattr(self, '_web_api'):
            raise RuntimeError('You must first call .get_base_web_api')
        if self._exists() and not self._final_object:
            self._web_api.refresh_from_db()
        return self._web_api
    
    def get_base_web_api(self):
        if self._exists():
            self._web_api = WebAPI.objects.get(view_code_name=self.view_code)
            if self._web_api.is_api != self._is_api:
                self._web_api.is_api = self._is_api
                self._web_api.save()
            self._final_object = getattr(self, '_final_object', False)
        else:
            self._web_api = WebAPI(view_code_name=self.view_code, is_api=self.is_api, view_name=self.view_name)
            self._final_object = False
        return self.web_api
    
    def refresh_version(self):
        if self._exists():
            self._web_api.refresh_from_db()
    
    def _exists(self):
        return WebAPI.objects.filter(view_code_name=self.view_code).exists()
    
    def available(self):
        if not self._exists():
            return False
        return self.web_api.available
    
    def control_version(self):
        if self.available():
            return
        if not self._exists():
            return self.not_registered()
        if self.web_api.is_deprecated():
            if self.web_api.new_compatible_view is not None:
                if self.web_api.new_compatible_view.url:
                    return HttpResponsePermanentRedirect(self.web_api.new_compatible_view.url)
            return self.gone_response()
        if self.web_api.coming_soon():
            return self.coming_soon_response()
    
    def coming_soon_response(self):
        return Response(status=status.HTTP_425_TOO_EARLY) if self.web_api.is_api else HttpResponse(
            status=status.HTTP_425_TOO_EARLY)
    
    def gone_response(self):
        return Response(status=status.HTTP_410_GONE) if self.web_api.is_api else HttpResponseGone()
    
    def not_registered(self):
        if self.require_register:
            if self.web_api:
                error = {
                    'code': 'not_registered',
                    'detail': _("Please first register your api view"),
                }
                if getattr(self, 'register_help_text', None) is not None:
                    error['help'] = getattr(self, 'register_help_text')
                
                return Response(error, status=status.HTTP_404_NOT_FOUND)
            raise Http404(_("Not Registered"))
        else:
            warnings.warn(NotRegisteredWarning(f'Not Registered! Please Register {self.view_code} at {self.__class__}'),
                          category=NotRegisteredWarning)
