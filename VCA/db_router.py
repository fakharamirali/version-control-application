from . import models
from .apps import VcaConfig


class RedirectToVersionDBRouter:
    def db_for_read(self, model, **hints):
        if isinstance(model._meta.app_config, VcaConfig):
            return 'version'
    
    def db_for_write(self, model, **hints):
        if isinstance(model._meta.app_config, VcaConfig):
            return 'version'
    
    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == 'version':
            if obj2._state.db != 'version':
                return False
            return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "version":
            if hints.get("model") in models.main_models:
                return True
        elif db == "default":
            if hints.get("model") in models.main_models:
                return False
