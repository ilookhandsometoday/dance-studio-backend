import secrets

def generate_response(result_code: int, message):
    return {'result_code': result_code, 'message': message, 'data':{}}

def generate_token(prefix: str = 'ust'):
    return prefix + '-' + secrets.token_hex(48)
