from PIL import Image


def crop_center(image_path, top_percent: float = 0):
    img = Image.open(image_path)
    w, h = img.size

    size = w
    top = int(h * top_percent / 100)

    left = 0
    right = w
    bottom = top + size

    if bottom > h:
        bottom = h
        top = h - size
        if top < 0:
            top = 0

    return img.crop((left, top, right, bottom))
