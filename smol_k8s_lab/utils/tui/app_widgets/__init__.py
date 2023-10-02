def placeholder_grammar(key: str):
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
        return f"enter comma seperated list of {key}"
    else:
        return f"enter {article} {key}"
