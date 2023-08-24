from django.conf import settings
from django.core.checks import register, Error, Tags, Warning
from django.utils.module_loading import import_string

from . import models


@register(Tags.compatibility)
def check_using_db_router(app_configs, **kwargs):
    errors = []
    if not getattr(settings, "DATABASE_ROUTERS", []):
        errors.append(
            Error(
                "DATABASE_ROUTER is empty",
                hint="""Please set DATABASE_ROUTER = ['VCA.db_router.RedirectToVersionDBRouter']""",
                id="VCA.E001",
            )
        )
    else:
        if "VCA.db_router.RedirectToVersionDBRouter" in settings.DATABASE_ROUTERS:
            for model in models.main_models:
                for router_name in settings.DATABASE_ROUTERS:
                    router = import_string(router_name)()
                    db_write = router.db_for_write(model)
                    db_read = router.db_for_read(model)
                    if db_write is db_read is None:
                        continue
                    if not (db_write == db_read == 'version'):
                        errors.append(
                            Error(
                                "Your DATABASE_ROUTERS order is invalid",
                                hint=f"Please put 'VCA.db_router.RedirectToVersionDBRouter' before '{router_name}'"
                                     f" in DATABASE_ROUTERS",
                                id="VCA.E002",
                            )
                        )
                    else:
                        if router_name != 'VCA.db_router.RedirectToVersionDBRouter':
                            errors.append(
                                Warning(
                                    f"Version's models routed by '{router_name}' "
                                    f"while 'VCA.db_router.RedirectToVersionDBRouter' in routers",
                                    hint=f"better to put 'VCA.db_router.RedirectToVersionDBRouter' "
                                         f"before '{router_name}'",
                                    id="VCA.W001",
                                )
                            )
                    break
                else:
                    errors.append(
                        Error(
                            f"No Route To DB for '{model.__name__}'",
                            id="VCA.E003"
                        )
                    )
        else:
            for model in models.main_models:
                for router_name in settings.DATABASE_ROUTERS:
                    router = import_string(router_name)()
                    db_write = router.db_for_write(model)
                    db_read = router.db_for_read(model)
                    if db_write is db_read is None:
                        continue
                    if not (db_write == db_read == 'version'):
                        errors.append(
                            Error(
                                "Your DATABASE_ROUTERS order is invalid",
                                hint="Please write 'VCA.db_router.RedirectToVersionDBRouter' in DATABASE_ROUTERS",
                                id="VCA.E004",
                            )
                        )
                    break
                else:
                    errors.append(
                        Error(
                            "Your DATABASE_ROUTERS order is invalid",
                            hint="Please write 'VCA.db_router.RedirectToVersionDBRouter' in DATABASE_ROUTERS",
                            id="VCA.E004",
                        )
                    )
    if 'version' not in settings.DATABASES:
        errors.append(
            Error(
                "Database version does not exists",
                hint="Please add version database in DATABASES",
                id="VCA.E005",
            )
        )
    return errors
