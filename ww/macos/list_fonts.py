from CoreText import (
    CTFontManagerCopyAvailableFontDescriptors,
    CTFontDescriptorCopyAttribute,
    kCTFontNameAttribute,
)


def list_fonts():
    font_descriptors = CTFontManagerCopyAvailableFontDescriptors()

    font_names = set()

    for descriptor in font_descriptors:
        font_name = CTFontDescriptorCopyAttribute(descriptor, kCTFontNameAttribute)
        if font_name:
            font_names.add(str(font_name))

    for name in sorted(font_names):
        print(name)


def main():
    try:
        list_fonts()
    except Exception as e:
        print(f"Error: {e}")
