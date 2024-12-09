import requests

with open("csr.pem", "rb") as f:
    csr_data = f.read()

url = "https://ca.haram.ru/csr"


files = {"csr": ("csr.pem", csr_data, "application/x-pem-file")}
headers = {"Authorization": "Bearer <token>"}

response = requests.post(url, files=files, headers=headers)
if response.status_code == 200:
    with open("signed_cert.pem", "wb") as cert_file:
        cert_file.write(response.content)
    print("Клиентский сертификат успешно получен и сохранён.")
else:
    print(f"Error: {response.status_code} - {response.text}")
