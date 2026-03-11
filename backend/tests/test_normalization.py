from gymdb.domain.processing import normalize_name

def test_normalize_basic():
    assert normalize_name("  Hello World  ") == "hello_world"
    assert normalize_name("GymDB Test") == "gymdb_test"
    assert normalize_name("Normalize-This_Name!") == "normalize_this_name"

def test_normalize_whitespace():
    assert normalize_name("   Leading and trailing spaces   ") == "leading_and_trailing_spaces"
    assert normalize_name("\nNew\nLine\nCharacters\n") == "new_line_characters"
    assert normalize_name("\tTabs\tand\tSpaces\t") == "tabs_and_spaces"

def test_normalize_symbols():
    assert normalize_name("Special@#%&*Characters") == "special_characters"
    assert normalize_name("Mix_of-Symbols_and Spaces!") == "mix_of_symbols_and_spaces"
    assert normalize_name("123Numbers456") == "123numbers456"

