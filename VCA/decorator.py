from .mixins import VersionControlMixin


def version_control(view_code, view_name: str = None, require_register: bool = False, is_api=None):
    version_controller = VersionControlMixin()
    version_controller.view_code = view_code
    version_controller.view_name = view_name
    version_controller.require_register = require_register
    version_controller._is_api = is_api
    version_controller.get_base_web_api()

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            version_controller.refresh_version()
            if not version_controller.available():
                return version_controller.control_version()
            else:
                return func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
