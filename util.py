import re

re_url = re.compile("[a-zA-z]+://\S*")


def is_url(text):
    if re_url.search(text):
        return True
    else:
        return False
