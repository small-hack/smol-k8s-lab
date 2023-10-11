def placeholder_grammar(key: str) -> str:
    """
    generates a grammatically correct placeolder string for inputs
    """
    article = ""

    # check if this is a plural (ending in s) and if ip address pool
    plural = key.endswith('s') or key == "address_pool"
    if plural:
        plural = True

    # check if the key starts with a vowel
    starts_with_vowel = key.startswith(('o','a','e'))

    # create a gramatically corrrect placeholder
    if starts_with_vowel and not plural:
        article = "an"
    elif not starts_with_vowel and not plural:
        article = "a"

    # if this is plural change the grammar accordingly
    if plural:
        return f"Please enter a comma seperated list of {key}"
    else:
        return f"Please enter {article} {key}"


def create_sanitized_list(input_value: str) -> list:
    """
    take string and split by , or ' ' if there are any in it. returns list of
    items if no comma or space in string, returns list with string as only index
    """

    # split by comma, thereby generating a list from a csv
    if "," in input_value:
        input_value = input_value.replace(" ","")
        value = input_value.split(",")

    # split by spaces, thereby generating a list from a space delimited list
    elif "," not in input_value and " " in input_value:
        value = input_value.split(" ")

    # otherwise just use the value
    else:
        value = [input_value]

    return value
