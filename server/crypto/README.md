# HSE DSA CRYPTO

## Usage

```python
dsa = GostDSA()
private_key, public_key = dsa.generate_key_pair()

signature = dsa.sign(b'test', private_key)
g.check(signature, b'test', public_key) # True
```

## Install

```bash
poetry add dist/hsecrypto-0.1.0-py3-none-any.whl
```
or
```bash
pip install dist/hsecrypto-0.1.0-py3-none-any.whl
```