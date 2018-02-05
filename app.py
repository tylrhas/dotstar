# pylint: disable=invalid-name
# pylint: disable=missing-docstring
import os
import RPi.GPIO as GPIO, Image, time
from flask import Flask, render_template, request
app = Flask(__name__)
app.debug = True
paint = True

def getFiles():
    path = "images"
    images = []
    for image in os.listdir(path):
        if os.path.isfile(os.path.join(path, image)):
            images.append(image)
    return images

@app.route("/")
def index():
    images = getFiles()
    return render_template('home.html', images=images)

@app.route("/stop", methods=['POST'])
def stop():
    # not sure if this will work as a method to stop the painting
    paint = False
    return "stopping"

@app.route("/start", methods=['POST'])
def start():
    # Set Paint to true so we can paint
    paint = True
    # Light painting / POV demo for Raspberry Pi using
    # Adafruit Digital Addressable RGB LED flex strip.
    # ----> http://adafruit.com/products/306

    # Configurable values
    filename  = 'images/'+ request.get_json()['filename']
    dev       = "/dev/spidev0.0"

    # Open SPI device, load image in RGB format and get dimensions:
    spidev    = file(dev, "wb")
    print "Loading..."
    img       = Image.open(filename).convert("RGB")
    pixels    = img.load()
    width     = img.size[0]
    height    = img.size[1]
    print "%dx%d pixels" % img.size
    # To do: add resize here if image is not desired height

    # Calculate gamma correction table.  This includes
    # LPD8806-specific conversion (7-bit color w/high bit set).
    gamma = bytearray(256)
    for i in range(256):
        gamma[i] = 0x80 | int(pow(float(i) / 255.0, 2.5) * 127.0 + 0.5)

    # Create list of bytearrays, one for each column of image.
    # R, G, B byte per pixel, plus extra '0' byte at end for latch.
    print "Allocating..."
    column = [0 for x in range(width)]
    for x in range(width):
        column[x] = bytearray(height * 3 + 1)

    # Convert 8-bit RGB image into column-wise GRB bytearray list.
    print "Converting..."
    for x in range(width):
        for y in range(height):
            value = pixels[x, y]
            y3 = y * 3
            column[x][y3]     = gamma[value[1]]
            column[x][y3 + 1] = gamma[value[0]]
            column[x][y3 + 2] = gamma[value[2]]


    # Then it's a trivial matter of writing each column to the SPI port.
    print "Displaying..."
    while True:
        for x in range(width):
            spidev.write(column[x])
            print x
            spidev.flush()
            time.sleep(0.001)
        time.sleep(0.5)

if __name__ == '__main__':
    app.run(host='0.0.0.0')