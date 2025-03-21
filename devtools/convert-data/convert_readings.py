def sign_extend_20bit(value):
    if value & 0x80000:
        value |= 0xFFF00000
    return value if value < (1 << 31) else value - (1 << 32)

def parse_reading(chunk):
    x = (chunk[0] << 12) | (chunk[1] << 4) | (chunk[2] >> 4)
    y = (chunk[3] << 12) | (chunk[4] << 4) | (chunk[5] >> 4)
    z = (chunk[6] << 12) | (chunk[7] << 4) | (chunk[8] >> 4)
    return sign_extend_20bit(x), sign_extend_20bit(y), sign_extend_20bit(z)

def main():
    filename = input("Enter the filename containing the hex string: ").strip()

    try:
        with open(filename, 'r') as f:
            hex_input = f.read().strip().replace(" ", "").replace("\n", "")
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return

    expected_length = 9 * 250 * 2  # 4500 hex characters
    if len(hex_input) != expected_length:
        print(f"Error: Expected {expected_length} hex characters, got {len(hex_input)}")
        return

    byte_data = bytes.fromhex(hex_input)
    readings = [parse_reading(byte_data[i:i+9]) for i in range(0, len(byte_data), 9)]

    for i, (x, y, z) in enumerate(readings):
        print(f"Reading {i+1}: X={(x/256000) * 9.81}, Y={(y/256000) * 9.81}, Z={(z/256000) * 9.81}")

if __name__ == "__main__":
    main()
