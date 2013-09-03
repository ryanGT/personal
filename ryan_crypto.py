import Crypto
reload(Crypto)
from Crypto.PublicKey import RSA
from Crypto import Random

def load_key(rsa_path):
    key = Crypto.PublicKey.RSA.importKey(open(rsa_path, 'r').read())
    return key


def encrypt_and_save(key, text, filename):
    pub_key = key.publickey()
    data = pub_key.encrypt(text,32)

    f = open(filename,'wb')
    f.write(data[0])
    f.close()


def read_file_contents(filepath):
    f = open(filepath,'rb')
    data = f.read()
    f.close()
    return data


def decrypt(key, encrypted):
    out = key.decrypt(encrypted)
    return out

