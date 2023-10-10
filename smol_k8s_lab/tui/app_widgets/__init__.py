def placeholder_grammar(key: str) -> str:
    """
    fixes the placeholder grammar for any given key
    """
    article = ""

    # make sure this isn't a plural key
    plural = key.endswith('s')

    if key == "address_pool":
        plural = True

    # create a gramatically corrrect placeholder
    if key.startswith(('o','a','e')) and not plural:
        article = "an"
    elif not plural:
        article = "a"

    # if this is plural
    if plural:
        return f"Please enter a comma seperated list of {key}"
    else:
        return f"Please enter {article} {key}"


def create_sanitized_list(input_value: str) -> list:
    """
    take string and split by , or ' ' if there are any in it. returns list of items
    if no comma or space in string, returns list with string as only index.
    """

    # split by , generating a list from a csv
    if "," in input_value:
        input_value = input_value.strip()
        value = input_value.split(", ")

    # split by spaces, generating a list from a space delimited list
    elif "," not in input_value and " " in input_value:
        value = input_value.split(" ")

    # otherwise just use the value
    else:
        value = [input_value]

    return value
