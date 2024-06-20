from django import forms
from django.core.exceptions import ValidationError
from django_filters import fields
from django_filters import rest_framework as filters


class FormModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def _check_values(self, value):
        """
        This is to patch django.forms.models.ModelMultipleChoiceField._check_values
        """
        key = self.to_field_name or "pk"
        # deduplicate given values to avoid creating many querysets or
        # requiring the database backend deduplicate efficiently.
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )
        for pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except (ValueError, TypeError):
                raise ValidationError(
                    self.error_messages["invalid_pk_value"],
                    code="invalid_pk_value",
                    params={"pk": pk},
                )

        qs = self.queryset.filter(**{"%s__in" % key: value})

        # ** The following is the original code that we removed **
        # pks = {str(getattr(o, key)) for o in qs}
        # for val in value:
        #     if str(val) not in pks:
        #         raise ValidationError(
        #             self.error_messages["invalid_choice"],
        #             code="invalid_choice",
        #             params={"value": val},
        #         )
        return qs


class FilterModelMultipleChoiceField(
    fields.ModelMultipleChoiceField, FormModelMultipleChoiceField
):
    """
    Patch the class inheritance
    so that django_filters.fields.ModelMultipleChoiceField._check_values method
    calls the api.filters.patch.FormModelMultipleChoiceField._check_values method
    instead of the django.forms.models.ModelMultipleChoiceField._check_values method
    """

    pass


class ModelMultipleChoiceFilter(filters.ModelMultipleChoiceFilter):
    field_class = FilterModelMultipleChoiceField
