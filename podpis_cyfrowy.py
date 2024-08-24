from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA3_256


def read_pdf_file(file_path):
    with open(file_path, 'rb') as file:
        pdf_bytes = file.read()
    return pdf_bytes

def modify_pdf_file(file_path):
    with open(file_path, 'ab') as file:
        file.write(b'\n Modified content')

def hash_message(message: bytes) -> bytes:
    h = SHA3_256.new(message)
    return h

def sign_message(private_key, message_hash):
    signature = pkcs1_15.new(private_key).sign(message_hash)
    return signature

def verify_signature(public_key, signature, message_hash):
    try:
        pkcs1_15.new(public_key).verify(message_hash, signature)
        print("Podpis jest ważny.")
    except (ValueError, TypeError):
        print("Podpis jest nieważny.")


mykeypriv2 = RSA.generate(1024)
mykeypub2 = mykeypriv2.publickey()


# with open('private_key.pem', 'rb') as f:
#     private_key_bytes = f.read()
    
# with open('public_key.pem', 'rb') as f:
#     public_key_bytes = f.read()

# private_key = RSA.import_key(private_key_bytes)
# public_key = RSA.import_key(public_key_bytes)

pwd = b'secret'
with open("myprivatekey.pem", "rb") as f:
    data = f.read()
    mykeypriv = RSA.import_key(data, pwd)

with open("mypublickey.pem", "rb") as f:
    data = f.read()
    mykeypub = RSA.import_key(data)    


message = b"Example message for signing"
message_hash = hash_message(message)

signature = sign_message(mykeypriv, message_hash)

# Wiadomość po stronie odbiorcy
message = b"Example message for signing"
message_hash = hash_message(message)

verify_signature(mykeypub, signature, message_hash)


pdf_file_path = 'decyzja.pdf' 
pdf_bytes = read_pdf_file(pdf_file_path)

pdf_hash = hash_message(pdf_bytes)

pdf_signature = sign_message(mykeypriv, pdf_hash)

print("Weryfikacja podpisu przed modyfikacją pliku:")
verify_signature(mykeypub, pdf_signature, pdf_hash)

modify_pdf_file(pdf_file_path)

modified_pdf_bytes = read_pdf_file(pdf_file_path)

modified_pdf_hash = hash_message(modified_pdf_bytes)

print("Weryfikacja podpisu po modyfikacji pliku:")
verify_signature(mykeypub, pdf_signature, modified_pdf_hash)
