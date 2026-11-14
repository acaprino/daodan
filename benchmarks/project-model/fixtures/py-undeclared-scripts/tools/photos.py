from PIL import Image

from helpers import thumb_size


def thumb(path):
    img = Image.open(path)
    img.thumbnail(thumb_size())
    return img
