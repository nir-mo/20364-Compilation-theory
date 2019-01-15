
def is_lark_token(obj):
    try:
        _, _ = obj.type, obj.value
        return True

    except AttributeError:
        return False