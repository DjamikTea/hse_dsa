import copy
import struct

IV_512 = bytes.fromhex(
    "8e20faa72ba0b4708b9c692f6a9d90f2"
    + "7f33d0e448c0f3ff0333a9d62c1b3f89"
    + "4a2c8b163e1d9d1e52cc0f133c90837f"
    + "1d95b0a144d3cdb71de0a8a1f611a62c"
)

IV_256 = bytes.fromhex(
    "9e8ba222b2a3f104a8fa31bb8db5f5ed"
    + "63a6cf963b7b43c4b35b626b0b5c3e41"
    + "d0c242bda01d8b3b949121aad2e9ae13"
    + "c579982af1b42b2d3721b5b74dff0f8e"
)

C = [
    bytes.fromhex(
        "b1085bda1ecadae9ebcb2f81c0657c1f2f6a76432e45d016714eb88d7585c4fc4b7ce09192676901a2422a08a460d31505767436cc744d23dd806559f2a64507"
    ),
    bytes.fromhex(
        "6fa3b58aa99d2f1a4fe39d460f70b5d7f3feea720a232b9861d55e0f16b501319ab5176b12d699585cb561c2db0aa7ca55dda21bd7cbcd56e679047021b19bb7"
    ),
    bytes.fromhex(
        "f574dcac2bce2fc70a39fc286a3d843506f15e5f529c1f8bf2ea7514b1297b7bd3e20fe490359eb1c1c93a376062db09c2b6f443867adb31991e96f50aba0ab2"
    ),
    bytes.fromhex(
        "ef1fdfb3e81566d2f948e1a05d71e4dd488e857e335c3c7d9d721cad685e353fa9d72c82ed03d675d8b71333935203be3453eaa193e837f1220cbebc84e3d12e"
    ),
    bytes.fromhex(
        "4bea6bacad4747999a3f410c6ca923637f151c1f1686104a359e35d7800fffbdbfcd1747253af5a3dfff00b723271a167a56a27ea9ea63f5601758fd7c6cfe57"
    ),
    bytes.fromhex(
        "ae4faeae1d3ad3d96fa4c33b7a3039c02d66c4f95142a46c187f9ab49af08ec6cffaa6b71c9ab7b40af21f66c2bec6b6bf71c57236904f35fa68407a46647d6e"
    ),
    bytes.fromhex(
        "f4c70e16eeaac5ec51ac86febf240954399ec6c7e6bf87c9d3473e33197a93c90992abc52d822c3706476983284a05043517454ca23c4af38886564d3a14d493"
    ),
    bytes.fromhex(
        "9b1f5b424d93c9a703e7aa020c6e41414eb7f8719c36de1e89b4443b4ddbc49af4892bcb929b069069d18d2bd1a5c42f36acc2355951a8d9a47f0dd4bf02e71e"
    ),
    bytes.fromhex(
        "378f5a541631229b944c9ad8ec165fde3a7d3a1b258942243cd955b7e00d0984800a440bdbb2ceb17b2b8a9aa6079c540e38dc92cb1f2a607261445183235adb"
    ),
    bytes.fromhex(
        "abbedea680056f52382ae548b2e4f3f38941e71cff8a78db1fffe18a1b3361039fe76702af69334b7a1e6c303b7652f43698fad1153bb6c374b4c7fb98459ced"
    ),
    bytes.fromhex(
        "7bcd9ed0efc889fb3002c6cd635afe94d8fa6bbbebab076120018021148466798a1d71efea48b9caefbacd1d7d476e98dea2594ac06fd85d6bcaa4cd81f32d1b"
    ),
    bytes.fromhex(
        "378ee767f11631bad21380b00449b17acda43c32bcdf1d77f82012d430219f9b5d80ef9d1891cc86e71da4aa88e12852faf417d5d9b21b9948bc924af11bd720"
    ),
]

A = [
    bytes.fromhex("8E20FAA72BA0B470"),
    bytes.fromhex("47107DDD9B505A38"),
    bytes.fromhex("AD08B0E0C3282D1C"),
    bytes.fromhex("D8045870EF14980E"),
    bytes.fromhex("6C022C38F90A4C07"),
    bytes.fromhex("3601161CF205268D"),
    bytes.fromhex("1B8E0B0E798C13C8"),
    bytes.fromhex("83478B07B2468764"),
    bytes.fromhex("A011D380818E8F40"),
    bytes.fromhex("5086E740CE47C920"),
    bytes.fromhex("2843FD2067ADEA10"),
    bytes.fromhex("14AFF010BDD87508"),
    bytes.fromhex("0AD97808D06CB404"),
    bytes.fromhex("05E23C0468365A02"),
    bytes.fromhex("8C711E02341B2D01"),
    bytes.fromhex("46B60F011A83988E"),
    bytes.fromhex("90DAB52A387AE76F"),
    bytes.fromhex("486DD4151C3DFDB9"),
    bytes.fromhex("24B86A840E90F0D2"),
    bytes.fromhex("125C354207487869"),
    bytes.fromhex("092E94218D243CBA"),
    bytes.fromhex("8A174A9EC8121E5D"),
    bytes.fromhex("4585254F64090FA0"),
    bytes.fromhex("ACCC9CA9328A8950"),
    bytes.fromhex("9D4DF05D5F661451"),
    bytes.fromhex("C0A878A0A1330AA6"),
    bytes.fromhex("60543C50DE970553"),
    bytes.fromhex("302A1E286FC58CA7"),
    bytes.fromhex("18150F14B9EC46DD"),
    bytes.fromhex("0C84890AD27623E0"),
    bytes.fromhex("0642CA05693B9F70"),
    bytes.fromhex("0321658CBA93C138"),
    bytes.fromhex("86275DF09CE8AAA8"),
    bytes.fromhex("439DA0784E745554"),
    bytes.fromhex("AFC0503C273AA42A"),
    bytes.fromhex("D960281E9D1D5215"),
    bytes.fromhex("E230140FC0802984"),
    bytes.fromhex("71180A8960409A42"),
    bytes.fromhex("B60C05CA30204D21"),
    bytes.fromhex("5B068C651810A89E"),
    bytes.fromhex("456C34887A3805B9"),
    bytes.fromhex("AC361A443D1C8CD2"),
    bytes.fromhex("561B0D22900E4669"),
    bytes.fromhex("2B838811480723BA"),
    bytes.fromhex("9BCF4486248D9F5D"),
    bytes.fromhex("C3E9224312C8C1A0"),
    bytes.fromhex("EFFA11AF0964EE50"),
    bytes.fromhex("F97D86D98A327728"),
    bytes.fromhex("E4FA2054A80B329C"),
    bytes.fromhex("727D102A548B194E"),
    bytes.fromhex("39B008152ACB8227"),
    bytes.fromhex("9258048415EB419D"),
    bytes.fromhex("492C024284FBAEC0"),
    bytes.fromhex("AA16012142F35760"),
    bytes.fromhex("550B8E9E21F7A530"),
    bytes.fromhex("A48B474F9EF5DC18"),
    bytes.fromhex("70A6A56E2440598E"),
    bytes.fromhex("3853DC371220A247"),
    bytes.fromhex("1CA76E95091051AD"),
    bytes.fromhex("0EDD37C48A08A6D8"),
    bytes.fromhex("07E095624504536C"),
    bytes.fromhex("8D70C431AC02A736"),
    bytes.fromhex("C83862965601DD1B"),
    bytes.fromhex("641C314B2B8EE083"),
]

PI = [
    252,
    238,
    221,
    17,
    207,
    110,
    49,
    22,
    251,
    196,
    250,
    218,
    35,
    197,
    4,
    77,
    233,
    119,
    240,
    219,
    147,
    46,
    153,
    186,
    23,
    54,
    241,
    187,
    20,
    205,
    95,
    193,
    249,
    24,
    101,
    90,
    226,
    92,
    239,
    33,
    129,
    28,
    60,
    66,
    139,
    1,
    142,
    79,
    5,
    132,
    2,
    174,
    227,
    106,
    143,
    160,
    6,
    11,
    237,
    152,
    127,
    212,
    211,
    31,
    235,
    52,
    44,
    81,
    234,
    200,
    72,
    171,
    242,
    42,
    104,
    162,
    253,
    58,
    206,
    204,
    181,
    112,
    14,
    86,
    8,
    12,
    118,
    18,
    191,
    114,
    19,
    71,
    156,
    183,
    93,
    135,
    21,
    161,
    150,
    41,
    16,
    123,
    154,
    199,
    243,
    145,
    120,
    111,
    157,
    158,
    178,
    177,
    50,
    117,
    25,
    61,
    255,
    53,
    138,
    126,
    109,
    84,
    198,
    128,
    195,
    189,
    13,
    87,
    223,
    245,
    36,
    169,
    62,
    168,
    67,
    201,
    215,
    121,
    214,
    246,
    124,
    34,
    185,
    3,
    224,
    15,
    236,
    222,
    122,
    148,
    176,
    188,
    220,
    232,
    40,
    80,
    78,
    51,
    10,
    74,
    167,
    151,
    96,
    115,
    30,
    0,
    98,
    68,
    26,
    184,
    56,
    130,
    100,
    159,
    38,
    65,
    173,
    69,
    70,
    146,
    39,
    94,
    85,
    47,
    140,
    163,
    165,
    125,
    105,
    213,
    149,
    59,
    7,
    88,
    179,
    64,
    134,
    172,
    29,
    247,
    48,
    55,
    107,
    228,
    136,
    217,
    231,
    137,
    225,
    27,
    131,
    73,
    76,
    63,
    248,
    254,
    141,
    83,
    170,
    144,
    202,
    216,
    133,
    97,
    32,
    113,
    103,
    164,
    45,
    43,
    9,
    91,
    203,
    155,
    37,
    208,
    190,
    229,
    108,
    82,
    89,
    166,
    116,
    210,
    230,
    244,
    180,
    192,
    209,
    102,
    175,
    194,
    57,
    75,
    99,
    182,
]

T = [
    0,
    8,
    16,
    24,
    32,
    40,
    48,
    56,
    1,
    9,
    17,
    25,
    33,
    41,
    49,
    57,
    2,
    10,
    18,
    26,
    34,
    42,
    50,
    58,
    3,
    11,
    19,
    27,
    35,
    43,
    51,
    59,
    4,
    12,
    20,
    28,
    36,
    44,
    52,
    60,
    5,
    13,
    21,
    29,
    37,
    45,
    53,
    61,
    6,
    14,
    22,
    30,
    38,
    46,
    54,
    62,
    7,
    15,
    23,
    31,
    39,
    47,
    55,
    63,
]


class GostHash:
    def __init__(self, message: bytes, is_256: bool = True):
        self.message = message
        self.is_256 = is_256

    def xor(self, a, b) -> bytes:
        assert len(a) == len(b)
        return bytes(i ^ j for i, j in zip(a, b))

    def S(self, x: bytes) -> bytes:
        return bytes(PI[b] for b in x)

    def P(self, x: bytes) -> bytes:
        return bytes(x[T[i]] for i in range(64))

    def L(self, a: bytes) -> bytes:
        input_u64 = [
            int.from_bytes(a[i : i + 8], byteorder="big") for i in range(0, 64, 8)
        ]

        buffers = [0] * 8

        for i in range(8):
            for j in range(64):
                if (input_u64[i] >> j) & 1 == 1:
                    buffers[i] ^= int.from_bytes(A[63 - j])

        buffer = b"".join(struct.pack(">Q", b) for b in buffers)
        res = [0] * 64
        for index, byte in enumerate(buffer):
            res[index] = byte

        return bytes(res)

    def X(self, k, a) -> bytes:
        return self.xor(k, a)

    def E(self, K, m) -> bytes:
        Ks = [K] * 13
        for i in range(1, 13):
            Ks[i] = self.L(self.P(self.S(self.xor(Ks[i - 1], C[i - 1]))))
        print(len(m))
        e = self.L(self.P(self.S(self.X(Ks[0], m))))
        es = []
        for i in range(1, 12):
            e = self.L(self.P(self.S(self.X(Ks[i], e))))
            es.append(e)
        e = self.X(Ks[12], e)
        return e

    def g_n(self, N, h, m):
        K = self.L(self.P(self.S(self.xor(h, N))))
        return self.xor(self.xor(self.E(K, m), h), m)

    def MSB(self, z: bytes, n: int = 256) -> bytes:
        return z[: n // 8]

    def hash(self) -> str:
        h = b"\x00" * 64
        N = b"\x00" * 64
        S = b"\x00" * 64

        while len(self.message) > 64:
            block = self.message[-64:]
            h = self.g_n(N, h, block)
            Nint = int.from_bytes(N) + len(self.message) * 8
            N = bytes.fromhex(hex(Nint)[2:].zfill(128))
            Sint = int.from_bytes(S) + int.from_bytes(block)
            S = bytes.fromhex(hex(Sint)[2:].zfill(128))
            print(S.hex())
            self.message = self.message[:-64]
        m = b"\x00" * (63 - len(self.message)) + b"\x01" + self.message
        h = self.g_n(N, h, m)
        Nint = int.from_bytes(N) + len(self.message) * 8
        N = bytes.fromhex(hex(Nint)[2:].zfill(128))
        Sint = int.from_bytes(S) + int.from_bytes(m)
        S = bytes.fromhex(hex(Sint)[2:].zfill(128))
        h = self.g_n(b"\x00" * 64, h, N)

        h = self.g_n(b"\x00" * 64, h, S)
        if self.is_256:
            h = self.MSB(h, 256)
        return h.hex()


# h = GostHash(message=bytes.fromhex("fbe2e5f0eee3c820fbeafaebef20fffbf0e1e0f0f520e0ed20e8ece0ebe5f0f2f120fff0eeec20f120faf2fee5e2202ce8f6f3ede220e8e6eee1e8f0f2d1202ce8f0f2e5e220e5d1"))
# print(h.hash())
# # print(h.L(bytes.fromhex("fcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfcfc")).hex())
