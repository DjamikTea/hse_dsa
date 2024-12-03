from hsecrypto import GostDSA
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import Name, NameAttribute, SubjectAlternativeName, DNSName
from cryptography.x509 import CertificateSigningRequestBuilder
from cryptography.x509.oid import NameOID

# создание пары ключей с использованием библиотеки hsecrypto
dsa = GostDSA()
private_key, public_key = dsa.generate_key_pair()


subject = Name([
    NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
    NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Moscow"),
    NameAttribute(NameOID.LOCALITY_NAME, u"Moscow"),
    NameAttribute(NameOID.ORGANIZATION_NAME, u"HSE"),
    NameAttribute(NameOID.COMMON_NAME, u"www.example.ru"),
])

csr = CertificateSigningRequestBuilder().subject_name(subject).add_extension(
    SubjectAlternativeName([DNSName(u"www.example.ru")]), critical=False
).sign( private_key, hashes.SHA256())

csr_pem = csr.public_bytes(serialization.Encoding.PEM)
with open("csr.pem", "wb") as f:
    f.write(csr_pem)

print("CSR успешно создан и сохранён в csr.pem")