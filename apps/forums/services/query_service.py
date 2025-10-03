"""Module store helpers for querysets."""


def convert_keywords_to_querytext(keywords_list: list) -> str:
    """Convert a word(s) list to formatted search query, use logical OR.

    Doc: https://www.postgresql.org/docs/current/textsearch-controls.html

    Example:
        >>> row = ['Dream stay', 'executive', 'newspaper', 'beyond optimizing']
        >>> convert_keywords_to_querytext(row)
        >>> "('Dream stay' | 'executive' | 'newspaper beyond' | 'optimizing')"
    One word `executive` be convert to "'executive'", what is valid

    """
    row = "' | '".join(keywords_list)
    return f"'{row}'"
