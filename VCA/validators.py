from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

__all__ = [
    'path_without_start_slash_validator', 'view_path_without_start_slash_validator',
    'view_path_validators', 'path_validators'
]

path_without_start_slash_validator = RegexValidator(r"^(?:(?!::).)*$")
path_with_start_slash_validator = RegexValidator(r"^/(?:(?!::).)*$", message=_("Your path is not started with '/'"))
view_path_without_start_slash_validator = RegexValidator(r"^[A-Za-z0-9/-_\.]+")
view_path_with_start_slash_validator = RegexValidator(r"^/[A-Za-z0-9/-_\.]+",
                                                      message=_("Your path is not started with '/'"))

path_validators = (path_without_start_slash_validator, path_with_start_slash_validator)
view_path_validators = (view_path_without_start_slash_validator, view_path_with_start_slash_validator)
