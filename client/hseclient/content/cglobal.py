data_dir = "data"
host_file = f"{data_dir}/host.json"
keys_file = f"{data_dir}/keys.json"
cert_file = f"{data_dir}/cert.json"
token_file = f"{data_dir}/token.json"
phone_number_file = f"{data_dir}/phone_number.json"
root_pubkey_file = f"{data_dir}/root_pubkey.json"
download_dir = "downloads"

def reassign_dir():
    global data_dir, host_file, keys_file, cert_file, token_file, phone_number_file, root_pubkey_file, download_dir
    host_file = f"{data_dir}/host.json"
    keys_file = f"{data_dir}/keys.json"
    cert_file = f"{data_dir}/cert.json"
    token_file = f"{data_dir}/token.json"
    phone_number_file = f"{data_dir}/phone_number.json"
    root_pubkey_file = f"{data_dir}/root_pubkey.json"