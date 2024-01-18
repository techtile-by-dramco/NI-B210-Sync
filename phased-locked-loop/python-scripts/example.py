import pll
import time 

p = pll.PLL()

p.set_LED_mode(pll.LED_MODE_LOCK_DETECT)

p.power_on()
p.enable_output()
p.frequency(500)

while not p.locked():
	print("Not locked")
	time.sleep(0.5)