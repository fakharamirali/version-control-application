from django.db.models.deletion import Collector


def restrict_or_upgrade(collector: Collector, field, sub_objs, using):
    for sub_obj in sub_objs:
        if sub_obj.web_api.new_compatible_view:
            collector.add_field_update(field, sub_obj.web_api.new_compatible_view, [sub_obj])
        else:
            collector.add_restricted_objects(field, [sub_obj])
            collector.add_dependency(field.remote_field.model, field.model)
