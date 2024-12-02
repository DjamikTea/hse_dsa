from dsa import GostDSA
from lib.curve import Point

if __name__ == "__main__":
    g = GostDSA()
    d, Q = g.generate_key_pair()
    
    sig = g.sign(b'test', d)
    print(d )
    print(g.check(sig, b'test', Q))
    print(Q)