from machine import Pin  # type: ignore[reportMissingImports]
import time

led = Pin(25, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_DOWN)

while True:
    if button.value():
        led.on()
    else:
        led.off()
    time.sleep(0.05)
