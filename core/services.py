from typing import Tuple, List, Dict, Any
from django.db import models


def model_update(
    *,
    instance: models.Model,
    fields: List[str],
    data: Dict[str, Any]
) -> Tuple[models.Model, bool]:
    has_updated = False
    updated_fields = []

    for field in fields:
        if field not in data:
            continue

        old_value = getattr(instance, field)
        new_value = data[field]

        if old_value != new_value:
            setattr(instance, field, new_value)
            has_updated = True
            updated_fields.append(field)

    if has_updated:
        instance.full_clean()
        updated_fields.append('updated_at')
        instance.save(update_fields=updated_fields)

    return instance, has_updated
