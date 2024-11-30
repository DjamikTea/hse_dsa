from dsa import GostDSA

if __name__ == "__main__":
    g = GostDSA()
    d, Q = g.generate_key_pair()
    
    sig = g.sign(b'test', d)
    print(sig)
    print(g.check(sig, b'test', Q))