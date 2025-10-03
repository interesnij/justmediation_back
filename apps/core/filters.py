from django.db.models.sql.constants import ORDER_PATTERN

from rest_framework.filters import OrderingFilter

import inflection
from admin_auto_filters.filters import \
    AutocompleteFilter as BaseAutocompleteFilter


def autocomplete_filter_class(field_name: str):
    """Create autocomplete filter for admin"""

    class AutocompleteFilter(BaseAutocompleteFilter):
        """Generated AutocompleteFilter."""

    AutocompleteFilter.title = inflection.humanize(
        word=field_name
    ).capitalize()
    AutocompleteFilter.field_name = field_name

    return AutocompleteFilter


class CustomOrderingFilter(OrderingFilter):

    def remove_invalid_fields(self, queryset, fields, view, request):
        """
        Considers actual field names along with
        verbose names as valid fields.
        """
        valid_fields = set(
            [
                f_name for f_tuple in
                self.get_valid_fields(queryset, view, {'request': request})
                for f_name in f_tuple
            ]
        )

        return [
            term for term in fields
            if term.lstrip('-') in valid_fields and ORDER_PATTERN.match(term)
        ]
