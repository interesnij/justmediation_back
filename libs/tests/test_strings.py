from ..strings import hide_except_last


def test_hide_except_last():
    """Test ``hide_except_last`` function, should return the same string in
    which all symbols replaces by '*' except last ``num`` which is 4 by
    default"""
    assert hide_except_last('TestTestTest') == '********Test'
