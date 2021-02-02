# Example of low-level Python wrapper for rpi_ws281x library.
# Author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
#
# This is an example of how to use the SWIG-generated _rpi_ws281x module.
# You probably don't want to use this unless you are building your own library,
# because the SWIG generated module is clunky and verbose.  Instead look at the
# high level Python port of Adafruit's NeoPixel Arduino library in strandtest.py.
#
# This code will animate a number of WS281x LEDs displaying rainbow colors.
import time
import random

import _rpi_ws281x as ws

blipSize = 12
LED_COUNT = 300

class Blip:
    def __init__(self, position):
        self.position = position
        self.duration = blipSize/2
        self.red = 0
        self.green = random.randint(16, 128)
        self.blue = 0

    def getOriginalSize(self):
        if self.duration > (blipSize/4):
            return ((blipSize/2)-self.duration)+1
        else:
            return self.duration/2
    
    def size(self):
        s = self.getOriginalSize()
        m = blipSize/2
        return (s*s*s)/(m)


    def update(self):
        self.duration -= 1

    def isFinished(self):
        return self.duration == 0

    def inRange(self, pos):
        s = self.size()
        return (self.position-s) < pos < (self.position+s)

    def getColour(self, pos):
        s = self.size()
        if (self.position-s) < pos < (self.position+s):
            return (self.green << 16) | (self.red << 8) | self.blue
        else:
            return 0

class Zap:
    def __init__(self, position, red, green, blue, tailLen, speed):
        self.position = position
        self.red = red
        self.green = green
        self.blue = blue
        self.tailLen = tailLen
        self.speed = speed

    def update(self):
        self.position -= self.speed

    def isFinished(self):
        return self.position <= -self.tailLen

    def inRange(self, pos):
        return self.position <= pos < (self.position + self.tailLen)

    def getColour(self, pos):
        if self.inRange(pos):
            attenuation = float(self.tailLen - pos + self.position) / self.tailLen
            colRed = int(round(self.red * attenuation))
            colGreen = int(round(self.green * attenuation))
            colBlue = int(round(self.blue * attenuation))
            return (colGreen << 16) | (colRed << 8) | colBlue
        else:
            return 0


def get_rand_col():
    return random.randint(0, 6) * 10


def get_rand_zap():
    return Zap(LED_COUNT, get_rand_col(), get_rand_col(), get_rand_col(), random.randint(3, 10),
               float(random.randint(15, 50)) / 10)

def get_rand_blip():
    return Blip(random.randint(0, LED_COUNT))

# LED configuration.
LED_CHANNEL = 1
LED_FREQ_HZ = 1200000  # Frequency of the LED signal.  Should be 800khz or 400khz.
LED_DMA_NUM = 10  # DMA channel to use, can be 0-14.
LED_GPIO = 18  # GPIO connected to the LED signal line.  Must support PWM!
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = 0  # Set to 1 to invert the LED signal, good if using NPN
# transistor as a 3.3V->5V level converter.  Keep at 0
# for a normal/non-inverted signal.

# Define colors which will be used by the example.  Each color is an unsigned
# 32-bit value where the lower 24 bits define the red, green, blue data (each
# being 8 bits long).
# DOT_COLORS = [  0x200000,   # red
# 				0x201000,   # orange
# 				0x202000,   # yellow
# 				0x002000,   # green
# 				0x002020,   # lightblue
# 				0x000020,   # blue
# 				0x100010,   # purple
# 				0x200010 ]  # pink

DOT_COLORS = [0x0000ff,  # blue
              0x000020,  # black
              0x000010,  # black
              0x000008,  # black
              0x000004,  # black
              0x000002,  # black
              0x000001,  # black
              0x000000,
              0x000000,
              0x000000]  # black

# Create a ws2811_t structure from the LED configuration.
# Note that this structure will be created on the heap so you need to be careful
# that you delete its memory by calling delete_ws2811_t when it's not needed.
leds = ws.new_ws2811_t()

# Initialize all channels to off
for channum in range(2):
    channel = ws.ws2811_channel_get(leds, channum)
    ws.ws2811_channel_t_count_set(channel, 0)
    ws.ws2811_channel_t_gpionum_set(channel, 0)
    ws.ws2811_channel_t_invert_set(channel, 0)
    ws.ws2811_channel_t_brightness_set(channel, 0)

channel0 = ws.ws2811_channel_get(leds, 0)
channel1 = ws.ws2811_channel_get(leds, 1)

ws.ws2811_channel_t_count_set(channel0, LED_COUNT)
ws.ws2811_channel_t_gpionum_set(channel0, LED_GPIO)
ws.ws2811_channel_t_invert_set(channel0, LED_INVERT)
ws.ws2811_channel_t_brightness_set(channel0, LED_BRIGHTNESS)

ws.ws2811_channel_t_count_set(channel1, LED_COUNT)
ws.ws2811_channel_t_gpionum_set(channel1, 13)
ws.ws2811_channel_t_invert_set(channel1, LED_INVERT)
ws.ws2811_channel_t_brightness_set(channel1, LED_BRIGHTNESS)

ws.ws2811_t_freq_set(leds, LED_FREQ_HZ)
ws.ws2811_t_dmanum_set(leds, LED_DMA_NUM)

# Initialize library with LED configuration.
resp = ws.ws2811_init(leds)
if resp != ws.WS2811_SUCCESS:
    message = ws.ws2811_get_return_t_str(resp)
    raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

zaps1 = []
zaps2 = []

# Wrap following code in a try/finally to ensure cleanup functions are called
# after library is initialized.
try:
    offset = 0
    while True:
        # Update each LED color in the buffer.
        for i in range(LED_COUNT):

            color = 0
            for zap in zaps1:
                if zap.inRange(i):
                    color |= zap.getColour(i)
            ws.ws2811_led_set(channel0, LED_COUNT - i, color)

            color = 0
            for zap in zaps2:
                if zap.inRange(i):
                    color |= zap.getColour(i)
            ws.ws2811_led_set(channel1, LED_COUNT - i, color)

            # Pick a color based on LED position and an offset for animation.
            # color = DOT_COLORS[(i + offset) % len(DOT_COLORS)]

            # Set the LED color buffer value.

        # Send the LED color data to the hardware.
        resp = ws.ws2811_render(leds)
        if resp != ws.WS2811_SUCCESS:
            message = ws.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))

        # Delay for a small period of time.
        #time.sleep(0.01)

        if random.randint(0, 40) == 0:
            zaps1.append(get_rand_zap())
        if random.randint(0,3) == 0:
            zaps1.append(get_rand_blip())

        if random.randint(0, 40) == 0:
            zaps2.append(get_rand_zap())
        if random.randint(0, 3) == 0:
            zaps2.append(get_rand_blip())

        # Move zaps up the line
        for z in zaps1:
            z.update()
            if z.isFinished():
                zaps1.remove(z)
        for z in zaps2:
            z.update()
            if z.isFinished():
                zaps2.remove(z)

        # Increase offset to animate colors moving.  Will eventually overflow, which
        # is fine.
        offset += 1

finally:
    # Ensure ws2811_fini is called before the program quits.
    ws.ws2811_fini(leds)
    # Example of calling delete function to clean up structure memory.  Isn't
    # strictly necessary at the end of the program execution here, but is good practice.
    ws.delete_ws2811_t(leds)
