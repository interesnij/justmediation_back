"""File with different utils classes and methods for DRF API."""
import re

from rest_framework_xml.parsers import XMLParser


class DocuSignXMLParser(XMLParser):
    """Custom XML parser for DocuSign.

    It defines specific for DocuSign xml `media_type` and performs some data
    cleaning after parsing.

    """
    media_type = 'text/xml; charset=utf-8'

    def parse(self, stream, media_type=None, parser_context=None):
        """Overridden original method to perform data cleaning after parsing.

        DocuSign XML file contains its related API link in all parsed keys.

        """
        data = super().parse(stream, media_type, parser_context)
        cleaned_data = self.clean_data({}, data)
        return cleaned_data

    def clean_data(self, cleaned: dict, original: dict):
        """Recursion to perform dict keys cleaning from HTML links."""
        for key, value in original.items():
            clean_key = re.sub(r'\{http[s]?://\S+\}', '', key)
            if isinstance(value, dict):
                cleaned[clean_key] = self.clean_data(
                    cleaned.get(key, {}),
                    value
                )
            else:
                cleaned[clean_key] = value
        return cleaned
