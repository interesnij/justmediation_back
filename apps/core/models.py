# from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import router
from django.db.models.deletion import (
    CASCADE,
    DO_NOTHING,
    PROTECT,
    Collector,
    get_candidate_relations_to_delete,
)

from model_utils.models import TimeStampedModel


class BaseModel(TimeStampedModel):
    """Base model for apps' models.

    This class adds to models created and modified fields
    """

    class Meta:
        abstract = True

    def clean(self):
        """Validate model data.

        First we collect all errors as dict and then if there any errors, we
        pass them ValidationError and raise it. By doing this django admin and
        drf can specify for each field an error.

        """
        errors = {}
        for field in self._meta.fields:
            clean_method = f'clean_{field.name}'
            if hasattr(self, clean_method):
                try:
                    getattr(self, clean_method)()
                except ValidationError as e:
                    errors[field.name] = e
        if errors:
            raise ValidationError(errors)

    @property
    def app_label(self):
        """Get model's app label."""
        return self._meta.app_label

    @property
    def model_name(self):
        """Get model's name."""
        return self._meta.model_name

    def remove(self, using=None, keep_parents=False):
        """Remove all instance related data, ignoring `PROTECT` on deletes.

        This method makes almost the same as `delete` method actions to remove
        some instance. It is useful in local, dev and stage envs to remove not
        needed test data from DB (shouldn't be used in production). It uses
        custom collector, which makes `CASCADE` action instead of `PROTECT`.

        """
        # make original data deletion in production env
        # Remove out temporary
        # if settings.ENVIRONMENT == 'production':
        #     return self.delete(using=using, keep_parents=keep_parents)

        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
            f'{self._meta.object_name} object can\'t be deleted because its '
            f'{self._meta.pk.attname} attribute is set to None.'
        )

        collector = RemoveCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()


class RemoveCollector(Collector):
    """Custom collector which performs CASCADE deletion instead of PROTECT.
    """

    def collect(
        self, objs, source=None, nullable=False, collect_related=True,
        source_attr=None, reverse_dependency=False, keep_parents=False
    ):
        """Method which collects related objects for deletion.

        Almost original `Collector` method, with the only difference in
        132-135 lines (add logic to use CASCADE deletion instead of PROTECT).

        """
        if self.can_fast_delete(objs):
            self.fast_deletes.append(objs)
            return
        new_objs = self.add(objs, source, nullable,
                            reverse_dependency=reverse_dependency)
        if not new_objs:
            return

        model = new_objs[0].__class__

        if not keep_parents:
            # Recursively collect concrete model's parent models, but not their
            # related objects. These will be found by meta.get_fields()
            concrete_model = model._meta.concrete_model
            for ptr in concrete_model._meta.parents.values():
                if ptr:
                    parent_objs = [getattr(obj, ptr.name) for obj in new_objs]
                    self.collect(parent_objs, source=model,
                                 source_attr=ptr.remote_field.related_name,
                                 collect_related=False,
                                 reverse_dependency=True)
        if collect_related:
            parents = model._meta.parents
            for related in get_candidate_relations_to_delete(model._meta):
                # Preserve parent reverse relationships if keep_parents=True.
                if keep_parents and related.model in parents:
                    continue
                field = related.field
                if field.remote_field.on_delete == DO_NOTHING:
                    continue
                batches = self.get_del_batches(new_objs, field)
                for batch in batches:
                    sub_objs = self.related_objects(related, batch)
                    if self.can_fast_delete(sub_objs, from_field=field):
                        self.fast_deletes.append(sub_objs)
                    elif sub_objs:
                        # main changes are here - add logic to use CASCADE
                        # deletion instead of PROTECT
                        original_on_delete = field.remote_field.on_delete
                        on_delete = original_on_delete \
                            if original_on_delete != PROTECT else CASCADE
                        on_delete(self, field, sub_objs, self.using)
            for field in model._meta.private_fields:
                if hasattr(field, 'bulk_related_objects'):
                    # It's something like generic foreign key.
                    sub_objs = field.bulk_related_objects(new_objs, self.using)
                    self.collect(sub_objs, source=model, nullable=True)
