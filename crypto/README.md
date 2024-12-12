# HSE DSA CRYPTO

## Usage

```python
dsa = GostDSA()
private_key, public_key = dsa.generate_key_pair()

signature = dsa.sign(b'test', private_key)
g.check(signature, b'test', public_key) # True
```

## Install

Download lib from [releases](https://github.com/DjamikTea/hse_dsa/releases/tag/0.2.1) and install

```bash
poetry add https://github.com/DjamikTea/hse_dsa/releases/download/0.1.1/hsecrypto-0.2.1-py3-none-any.whl
```

or

```bash
pip install https://github.com/DjamikTea/hse_dsa/releases/download/0.1.1/hsecrypto-0.2.1-py3-none-any.whl
```
