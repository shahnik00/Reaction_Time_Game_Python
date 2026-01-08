import machine
import time
import random
import utime
from lcd1602 import LCD

SEGCODE = [0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f]

sdi = machine.Pin(18,machine.Pin.OUT) #sdi(serial data input) is where the 1's and 0's go
rclk = machine.Pin(19,machine.Pin.OUT) #rclk(register clk) is the post button where when it pulses, the chip takes whatever is in memory and pushes it to the leds
srclk = machine.Pin(20,machine.Pin.OUT) #shift register clk is on posedge clk, shifts data down led

#we do this entire chunk because if we ever change the pins, we dont want to replace every spot it says pin #10
placePin = [] #create empty arr 
pin = [10,13,12,11] #create arr of pins 10-13
for i in range(4): 
    placePin.append(None) #adds placeholder - You cannot assign a value to placePin[0] if slot 0 doesn't exist yet.
    placePin[i] = machine.Pin(pin[i], machine.Pin.OUT)  #assigns the spot in the array to the object pin 10
#function that pickes which digit to show at one time - cant do all of them at once becuase all connected

def log_to_csv(mode, time_ms):
    try:
        # Open 'reaction_data.csv' in append mode ('a')
        with open('reaction_data.csv', 'a') as f:
            # Get a simple timestamp (seconds since boot)
            timestamp = int(time.ticks_ms() / 1000)
            # Write: Timestamp, Mode (Visual/Audio), Time
            f.write("{},{},{}\n".format(timestamp, mode, time_ms))
        print("Data saved: " + mode + " - " + str(time_ms))
    except Exception as e:
        print("Error saving data:", e)
        
def pickDigit(digit):
    for i in range(4): 
        placePin[i].value(1)
    placePin[digit].value(0)

def clearDisplay():
    hc595_shift(0x00)
    
def hc595_shift(dat): 
    rclk.low()
    time.sleep_us(200)
    for bit in range(7, -1, -1):
        srclk.low() #getting clk rdy
        time.sleep_us(200)
        value = 1 & (dat >> bit) #returns 1 bit of value, from most first to least, shifts the byte number 7 times, then 6, etc
        sdi.value(value) #sendning the data
        time.sleep_us(200)
        srclk.high() #shifts and caputrues data
        time.sleep_us(200)
    time.sleep_us(200)
    rclk.high() #leds change to what the data says
    
#displays the number but needs to put in in the array by each digit
def display(num):
    digits = [num % 10, (num // 10) % 10, (num // 100) % 10, (num // 1000) % 10] #this gets the ones place, then tens, etc. 
    
    for i in range(4):
        pickDigit(i) #this returns each of the numbers in the 4 digit number
        hc595_shift(SEGCODE[digits[i]]) #segcode at digits[i] is the secode of a number, which the segcode[8] is 0xfa for ex (hex) and get converted to binary which tells it which lights to turn on
        time.sleep_ms(1)  # Small delay for stable display

# Setup
buzzer = machine.PWM(machine.Pin(0))  # Initialize buzzer

# Red LEDs
led1 = machine.Pin(2, machine.Pin.OUT)
led2 = machine.Pin(3, machine.Pin.OUT)
led3 = machine.Pin(4, machine.Pin.OUT)
# Green LED
led4 = machine.Pin(5, machine.Pin.OUT)

# Buttons
button1 = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Initialize button1 with pull-down resistor
button2 = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Initialize button2 with pull-down resistor

# Switch
switch = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_DOWN)  # Initialize switch with pull-down resistor

# LCD Setup
lcd = LCD()  # Initialize the LCD
lcd.clear()  # Clear the LCD display

# Helper function to play a tone
def tone(pin, frequency, duration):
    pin.freq(frequency)  # Set the frequency of the buzzer
    pin.duty_u16(30000)  # Set the duty cycle
    utime.sleep_ms(duration)  # Play the tone for the specified duration
    pin.duty_u16(0)  # Stop the tone

# LED Game
def led_game():
    # Initialize the LEDs
    led3.value(0)  # red
    led4.value(1)  # green
    led1.value(0)  # red
    led2.value(0)  # red
    highest_value = None

    while button1.value() == 1 and led4.value() == 1: # makes sure that the first button is pressed and the green led is on 
        print("Starting LED game")
        utime.sleep(1)
        led4.value(0)
        utime.sleep(1)
        led1.value(1)
        utime.sleep(1)
        led2.value(1)
        utime.sleep(1)
        led3.value(1)
        rand = random.uniform(2, 6) # chooses a random sleep time before the green led turns on and the time starts
        utime.sleep(rand)
        led4.value(1)
        start = time.ticks_ms()

        while button2.value() == 0: # while the second button is not pressed the timer is running 
            elapsed = time.ticks_ms() - start
            count = int(elapsed / 10)
            display(count)
        
        end = time.ticks_ms()
        elapsed = end - start
        log_to_csv("Visual", elapsed)

        
        if highest_value is None or elapsed < highest_value: # if the time is less than the highest value than that is the new value
            highest_value = elapsed

        lcd.clear()
        lcd.message("Elapsed Time:\n" + str(elapsed) + "ms")
        utime.sleep(2)
        lcd.clear()
        lcd.message("Best Time:\n" + str(highest_value) + "ms")
        utime.sleep(2)
        
        print("Time stop")
        utime.sleep(2)

# Buzzer Game
def buzzer_game():
    highest_value = None

    while button1.value() == 1:
        print("Starting Buzzer game")
        rand = random.uniform(2, 6)
        utime.sleep(rand)
        tone(buzzer, 1000, 500)
        start = time.ticks_ms()

        while button2.value() == 0:
            elapsed = time.ticks_ms() - start
            count = int(elapsed / 10)
            display(count)

        end = time.ticks_ms()
        elapsed = end - start
        log_to_csv("Audio", elapsed)


        if highest_value is None or elapsed < highest_value:
            highest_value = elapsed

        lcd.clear()
        lcd.message("Elapsed Time:\n" + str(elapsed) + "ms")
        utime.sleep(2)
        lcd.clear()
        lcd.message("Best Time:\n" + str(highest_value) + "ms")
        utime.sleep(2)
        
        print("Time stop")
        utime.sleep(2)

# Main function
def main():
        try:
        with open('reaction_data.csv', 'r') as f:
            pass
    except OSError:
        with open('reaction_data.csv', 'w') as f:
            f.write("Timestamp,Mode,ReactionTime_ms\n")
    while True:
        # Reset LEDs
        led1.value(0)
        led2.value(0)
        led3.value(0)
        led4.value(0)
        
        if switch.value() == 1:
            led_game()
        else:
            buzzer_game()

# Run the main function
main()


