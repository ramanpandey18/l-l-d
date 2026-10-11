import random
import string


# characters used in short code — no confusing chars like 0/O, 1/l
CHARS = string.ascii_letters + string.digits  # a-z A-Z 0-9


def generate_short_code(length: int = 6) -> str:
    """
    Generate a random short code like 'aB3xYz'
    Length 6 gives 62^6 = 56 billion combinations
    """
    return "".join(random.choices(CHARS, k=length))
