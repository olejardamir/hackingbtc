import hashlib
import random
import secrets
import base58
from ecdsa import SigningKey, ellipticcurve
from ecdsa.curves import Curve
import time
import os
import multiprocessing

# Let's gather our crayons and color in the “Certicom secp256k1” curve with these magical numbers!
_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_b = 0x0000000000000000000000000000000000000000000000000000000000000007  # Here’s the 'b' ingredient in our curve recipe!
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # This giant number is our special boundary (the prime field)!
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798  # 'Gx' marks the x-position of our generator point!
_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8  # 'Gy' is the matching y-position of our generator point!
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # This is our ‘r’—the finishing line for big math dances!

# Now let's paint our special secp256k1 curve with these magical numbers!
curve_secp256k1 = ellipticcurve.CurveFp(_p, _a, _b, 1)

# This is our special generator point that helps us do the cryptography dance!
generator_secp256k1 = ellipticcurve.PointJacobi(
    curve_secp256k1, _Gx, _Gy, 1, _r, generator=True
)

# Let’s name this curve “SECP256k1” so we can use it whenever we like!
SECP256k1 = Curve(
    "SECP256k1",
    curve_secp256k1,
    generator_secp256k1,
    (1, 3, 132, 0, 10),
    "secp256k1",
)

# This little helper takes a super-secret key and turns it into a fancy Base58 Bitcoin address!
def private_key_to_address_original(private_key_hex):
    try:
        private_key_bytes = bytes.fromhex(private_key_hex)
        sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        vk = sk.get_verifying_key()
        public_key_bytes = vk.to_string("compressed")
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new("ripemd160")
        ripemd160_hash.update(sha256_hash)
        hashed_public_key = ripemd160_hash.digest()
        hashed_public_key_with_version = b'\x00' + hashed_public_key
        checksum = hashlib.sha256(hashlib.sha256(hashed_public_key_with_version).digest()).digest()[:4]
        binary_address = hashed_public_key_with_version + checksum
        address = base58.b58encode(binary_address).decode('utf-8')
        return address
    except:
        # If something goes wrong, we give back an empty string (like a lost treasure map!)
        return ''

# This helper returns our address as a big HEX string instead of Base58—like painting with different colors!
def private_key_to_address_hex(private_key_hex):
    private_key_bytes = bytes.fromhex(private_key_hex)
    sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
    vk = sk.get_verifying_key()
    public_key_bytes = vk.to_string("compressed")
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new("ripemd160")
    ripemd160_hash.update(sha256_hash)
    hashed_public_key = ripemd160_hash.digest()
    hashed_public_key_with_version = b'\x00' + hashed_public_key
    checksum = hashlib.sha256(hashlib.sha256(hashed_public_key_with_version).digest()).digest()[:4]
    binary_address = hashed_public_key_with_version + checksum
    # We return everything after the first byte in uppercase hex—a new style for our magical address
    return binary_address.hex()[2:].upper()

def universal_hex_to_address_hex(hex_str):
    """
    Hello, curious adventurer! This function takes ANY secret-hex you give it.
    1. If it’s already exactly 32 bytes long, we use it as is (like a perfect puzzle piece).
    2. If not, we shrink or stretch it with a SHA-256 ‘hug’ to make it exactly 32 bytes.
    3. We conjure a special compressed public key from that private key.
    4. We wave a hashing wand: SHA-256 then RIPEMD-160.
    5. We add a '0x00' friend in front and a special 4-byte checksum buddy at the end.
    6. We present the final result in hex form—no if/else magic needed explicitly!
    """
    # (A) Turn the hex string into real bytes, like unwrapping candy!
    input_bytes = bytes.fromhex(hex_str)

    # (B) If we already have 32 bytes, we keep them. If not, we turn them into 32 bytes with SHA-256!
    private_key_bytes = (
        input_bytes * (len(input_bytes) == 32) +
        hashlib.sha256(input_bytes).digest() * (len(input_bytes) != 32)
    )

    # (C) We use our private key to make a signing key
    sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
    vk = sk.get_verifying_key()

    # (D) Ta-da! We compress our public key—like folding a big paper into a small shape
    public_key_bytes = vk.to_string("compressed")

    # (E) Now we do two magic spells: SHA-256 then RIPEMD-160
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new("ripemd160")
    ripemd160_hash.update(sha256_hash)
    hashed_public_key = ripemd160_hash.digest()

    # (F) We put '0x00' in front, like a friendly helper
    hashed_with_version = b'\x00' + hashed_public_key

    # (G) We do double SHA-256 to get our 4-byte checksum…like checking our homework twice!
    double_sha = hashlib.sha256(hashlib.sha256(hashed_with_version).digest()).digest()
    checksum = double_sha[:4]

    # (H) We stick the puzzle pieces together and show it in hex—minus the first byte for style
    result_bytes = hashed_with_version + checksum
    return result_bytes.hex()[2:]

def universal_hex_to_64hex_digest(hex_str):
    """
    Welcome, friend! This function also takes any hex string you provide.
    1. If it’s exactly 32 bytes, we keep it.
    2. Otherwise, we hug it with SHA-256 until it becomes 32 bytes long.
    3. We get a compressed public key from that special private key.
    4. Then we do the magical SHA-256 → RIPEMD-160 dance!
    5. We add a '0x00' friend in front.
    6. We do double SHA-256 on those bytes (no truncating for a short checksum).
    7. We share ALL 32 bytes of that final SHA-256, giving you a 64-hex-digit treasure!
    """
    input_bytes = bytes.fromhex(hex_str)
    private_key_bytes = (
        input_bytes * (len(input_bytes) == 32) +
        hashlib.sha256(input_bytes).digest() * (len(input_bytes) != 32)
    )
    sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
    vk = sk.get_verifying_key()
    public_key_bytes = vk.to_string("compressed")
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new("ripemd160")
    ripemd160_hash.update(sha256_hash)
    hashed_public_key = ripemd160_hash.digest()
    with_version = b"\x00" + hashed_public_key
    first_sha = hashlib.sha256(with_version).digest()
    second_sha = hashlib.sha256(first_sha).digest()
    # Return the entire 32-byte second hash as 64 uppercase hex digits!
    return second_sha.hex().upper()

# This helper does something unusual: it ONLY uses SHA-256 on the compressed pubkey for its 'address.'
def private_key_to_custom_hex(private_key_hex):
    """
    This is NOT a standard address. Think of it like a fun experiment:
    1. We take the private key.
    2. We make a compressed pubkey.
    3. We do just a single SHA-256 on that pubkey (no RIPEMD-160).
    4. We add '0x00' in front and a double-SHA-256 checksum at the end.
    That’s it!
    """
    private_key_bytes = bytes.fromhex(private_key_hex)
    sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
    vk = sk.get_verifying_key()
    public_key_bytes = vk.to_string("compressed")
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    hashed_with_version = b'\x00' + sha256_hash
    checksum_full = hashlib.sha256(hashlib.sha256(hashed_with_version).digest()).digest()
    checksum = checksum_full[:4]
    result_bytes = hashed_with_version + checksum
    return result_bytes.hex()

# This friend decodes our fancy Base58-encoded addresses back into bytes so we can peek inside.
def decode_address(encoded_address):
    binary_address = base58.b58decode(encoded_address)
    return binary_address.hex()

# We replace one random character in a string with 'g'—like sprinkling a bit of silliness!
def replace_with_g(string):
    random_index = random.randint(0, len(string) - 1)  # Pick a random spot to be silly
    replaced_char = string[random_index]
    new_string = string[:random_index] + 'g' + string[random_index + 1:]
    return replaced_char, new_string

# Generate random hex of a certain length—like picking random crayons from a big box
def generate_random_hex(length):
    if length <= 0:
        # If we ask for 0 or negative, we say none
        return None
    num_bytes = (length + 1) // 2
    random_bytes = secrets.token_bytes(num_bytes)
    hex_string = random_bytes.hex()[:length]
    return hex_string

# This splits a string with commas—like making a comma-separated list of goodies
def split_by_comma(input_string):
    return ','.join(input_string)

# Let’s append a new line to a file, adding more magical words to the end
def append_to_file(file_path, new_string):
    with open(file_path, 'a') as file:
        file.write(new_string + '\n')

# This makes a CSV-like line with a random private key, a replaced char, and an address
def getCsvLine():
    pk = generate_random_hex(64)
    addr_hex = private_key_to_address_hex(pk)
    ch, pk_g = replace_with_g(pk)
    str_g = pk_g + '' + addr_hex + '' + ch
    ln = split_by_comma(str_g)
    return ln

# We redefine this here just to ensure we’re consistent with file writing
def append_to_file(file_path, new_string):
    with open(file_path, 'a') as file:
        file.write(new_string + '\n')

# Finding the midpoint between two 64-char hex strings (like drawing a line between two stars!)
def midpoint_hex(hex1: str, hex2: str) -> str:
    num1 = int(hex1, 16)
    num2 = int(hex2, 16)
    mid = (num1 + num2) // 2
    return f'{mid:064X}'

# Pick a random 64-hex number somewhere between two hex strings—like wandering between two points on a treasure map
def random_hex_between(start_hex: str, end_hex: str) -> str:
    start_int = int(start_hex, 16)
    end_int = int(end_hex, 16)
    if start_int > end_int:
        start_int, end_int = end_int, start_int
    random_int = random.randint(start_int, end_int)
    return f"{random_int:064X}"

# Compare two big hex strings: returns 1 if A is bigger, else 0—like a quick “who’s taller?” check
def compare_hex(A: str, B: str) -> int:
    return 1 if int(A, 16) > int(B, 16) else 0

# This changes a Base58 Bitcoin address into hex so we can see under the hood
def public_key_to_hex(public_key):
    try:
        binary_address = base58.b58decode(public_key)
        if len(binary_address) != 25:
            raise ValueError(f"Invalid address length: {len(binary_address)}")
        hashed_public_key_with_checksum = binary_address[1:]
        address_hex = hashed_public_key_with_checksum.hex()
        return address_hex.upper()
    except Exception as e:
        return f"Error: {e}"

# This takes a 24-hex chunk (20 bytes + 4 checksum) and a version byte, and creates a Base58 address
def hex_to_address(address_hex, version_byte=b'\x00'):
    try:
        hashed_pubkey_with_checksum = bytes.fromhex(address_hex)
        if len(hashed_pubkey_with_checksum) != 24:
            raise ValueError(f"Invalid address hex length: got {len(hashed_pubkey_with_checksum)}, expected 24")
        full_binary_address = version_byte + hashed_pubkey_with_checksum
        base58_address = base58.b58encode(full_binary_address)
        return base58_address.decode('utf-8')
    except Exception as e:
        return f"Error: {e}"


