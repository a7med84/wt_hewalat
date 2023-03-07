from openerp.http import request
from cryptography.fernet import Fernet


def decrypt(val):
        if isinstance(val, memoryview):
            val = bytes(val)
        if isinstance(val, str):
            val = val.encode('utf-8')
        fernet = Fernet(get_key())
        return fernet.decrypt(val).decode('utf8')


def get_key():
    headers = request.httprequest.headers
    return headers['X-SECRET-KEY']


