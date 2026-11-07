from pathlib import Path
import struct
import zlib

from pytest_bdd import given, scenarios, then, when

BRAND_DIR = Path(__file__).parents[1] / "custom_components" / "insnrg" / "brand"

scenarios("features/integration_branding.feature")


@given("the Insnrg integration branding assets", target_fixture="branding_assets")
def branding_assets():
    return BRAND_DIR


@when("I inspect the bundled local brand files", target_fixture="loaded_brand_images")
def loaded_brand_images(branding_assets):
    images = {}
    for name in ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png"):
        data = (branding_assets / name).read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        offset = 8
        chunks = []
        compressed = bytearray()
        width = height = color_type = bit_depth = None
        saw_end = False
        while offset < len(data):
            length = struct.unpack(">I", data[offset:offset + 4])[0]
            kind = data[offset + 4:offset + 8]
            start, end = offset + 8, offset + 8 + length
            payload = data[start:end]
            assert end + 4 <= len(data)
            checksum = struct.unpack(">I", data[end:end + 4])[0]
            assert zlib.crc32(kind + payload) & 0xFFFFFFFF == checksum
            chunks.append(kind)
            if kind == b"IHDR":
                width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
            elif kind == b"IDAT":
                compressed.extend(payload)
            elif kind == b"IEND":
                saw_end = True
                offset = end + 4
                break
            offset = end + 4
        assert saw_end and offset == len(data)
        assert chunks[0] == b"IHDR" and chunks[-1] == b"IEND"
        assert bit_depth == 8 and color_type == 6  # RGBA retains transparency.
        assert len(zlib.decompress(compressed)) == height * (1 + width * 4)
        images[name] = (width, height)
    return images


@then("square icons and landscape logos are available at standard resolutions")
def standard_brand_images(branding_assets, loaded_brand_images):
    expected = {
        "icon.png": (256, 256),
        "icon@2x.png": (512, 512),
        "logo.png": (712, 256),
        "logo@2x.png": (1424, 512),
    }
    for name, size in expected.items():
        path = branding_assets / name
        image_size = loaded_brand_images[name]
        assert path.is_file() and path.stat().st_size > 0
        assert image_size == size
