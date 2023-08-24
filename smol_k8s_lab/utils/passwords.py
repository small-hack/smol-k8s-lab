import secrets
import string
from random import randrange


def create_password(special_character: bool = False) -> str:
    """
    Generate a 32 alphanumeric password with at least one lowercase character,
    at least one uppercase character, and at least three digits:
    https://docs.python.org/3/library/secrets.html#recipes-and-best-practices

    Takes optional special_character bool. If true, sets a random character in
    the password string to . (period).

    returns password str
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(32))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break

    # if special character requested in the password, we'll replace a random
    # random character in the password string with periods
    if special_character:
        random_number = randrange(0,31)
        replace_character = password[random_number]
        password = password.replace(replace_character, '.')

    return password
