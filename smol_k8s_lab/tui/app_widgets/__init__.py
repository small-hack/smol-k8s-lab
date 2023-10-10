def create_sanitized_list(input_value: str) -> list:
    """
    take string and split by , or ' ' if there are any in it. returns list of
    items if no comma or space in string, returns list with string as only index
    """

    # split by comma, thereby generating a list from a csv
    if "," in input_value:
        input_value = input_value.strip()
        value = input_value.split(",")

    # split by spaces, thereby generating a list from a space delimited list
    elif "," not in input_value and " " in input_value:
        value = input_value.split(" ")

    # otherwise just use the value
    else:
        value = [input_value]

    return value
