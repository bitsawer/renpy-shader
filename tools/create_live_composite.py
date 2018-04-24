
"""
    Helper script for cropping images and creating a RenPy Composite for them.
    Quite specific and mostly useful for processing images exported from a
    rendering program like Blender or from Photoshop layers.

    Requires Pillow Python image processing library to be installed.

    Command line example (current working directory at the base of this project):

        python tools/create_live_composite.py ShaderDemo/game/images/doll

    This assumes all images in the source directory have the same size. The script
    crops them and creates an efficient Composite that can be used for rigging
    or just normally. The resulting Composite is written into a .rpy-file
    in the target directory.
"""

import sys
import os
from PIL import Image

IMAGES = ["png", "jpg"]
POSTFIX = "crop"
PAD = 5

sourceDir = sys.argv[1]
sourceImages = [os.path.join(sourceDir, name) for name in os.listdir(sourceDir) if name.lower().split(".")[-1] in IMAGES]
sourceImages.sort()

def findValidImages(images):
    valid = []
    size = None
    for path in sourceImages:
        image = Image.open(path)
        if POSTFIX and POSTFIX in path.lower():
            print("Skipping already cropped: %s" % path)
        elif size is None or image.size == size:
            size = image.size
            valid.append((path, image))
        else:
            print("Image %s has size %s, should be %s? Skipped." % (path, str(image.size), str(size)))
    return valid

def getCropRect(image):
    x = 0
    y = 0
    x2 = image.size[0]
    y2 = image.size[1]
    box = image.getbbox()
    if box:
        return max(box[0] - PAD, 0), max(box[1] - PAD, 0), min(box[2] + PAD, image.size[0]), min(box[3] + PAD, image.size[1])
    return x, y, x2, y2

def createName(path):
    parts = path.rsplit(".", 1)
    return parts[0] + POSTFIX + "." + parts[1]

results = []
for path, image in findValidImages(sourceImages):
    rect = getCropRect(image)
    cropped = image.crop(rect)
    name = createName(path)
    cropped.save(name)
    print("Saved: %s. Cropped: %s" % (name, str(rect)))
    results.append((name, image, rect))

name = os.path.normcase(sourceDir).split(os.sep)[-1]
with open(os.path.join(sourceDir, name + ".rpy"), "w") as f:
    base = results[0]

    f.write("#Automatically generated file\n\n")
    f.write("image %s = Composite(\n" % name)
    f.write("    (%i, %i),\n" % base[1].size)
    for result in results:
        name, image, crop = result
        name = name[name.find("images"):].replace("\\", "/")
        f.write("    (%i, %i), \"%s\",\n" % (crop[0], crop[1], name))
    f.write(")\n")
