#!/usr/bin/env python

import subprocess
import argparse
import time
import threading
import select
import tty
import termios
import sys
import os


# Default dimensions just in case
DEFAULT_HEIGHT = 24
DEFAULT_WIDTH = 80

# Arguments
parser = argparse.ArgumentParser(description="Fancy countdown script")

parser.add_argument("-m", "--minutes", action="store",
                    type=int, help="Number of minutes",
                    default=25)
parser.add_argument("-s", "--seconds", action="store",
                    type=int, help="Number of seconds",
                    default=0)
# Default font in the same folder
DEFAULT_FONT = os.path.dirname(os.path.realpath(__file__)) + "/font.txt"
parser.add_argument("-f", "--font", action="store",
                    help="Custom font file",
                    default=DEFAULT_FONT)
parser.add_argument("-n", "--nocenter", action="store_true",
                    help="Do not center timer (more efficient)")

args = parser.parse_args()

centered = not args.nocenter
seconds = args.seconds
minutes = args.minutes
fontFile = args.font

seconds = minutes * 60 + seconds


# Turn string into blocky ascii representation
# Supports 0-9, colon
def asciiFormat(string, font):
    # enumerate numbers and colons
    string = list(map(int, [c.replace(":", "10") for c in list(string)]))
    height = len(font[0])

    frame = ""
    # fill frame top to bottom
    for i in range(height):
        for char in string[:-1]:
            frame += font[char][i] + " "
        # dirty hack to have no space at the end
        frame += font[string[-1]][i]

        frame += "\n"
    return frame[:-1]


# Pad with spaces and newlines to center
def center(frame, termDimensions):
    if centered:
        termHeight = termDimensions[0]
        termWidth = termDimensions[1]
        frame = frame.split("\n")
        frameWidth = max(map(len, frame))
        frameHeight = len(frame)
        # pad horizontally
        pad = " " * int((termWidth - frameWidth) / 2)
        frame = "\n".join([(pad + line + pad) for line in frame])

        # pad vertically
        pad = "\n" * int((termHeight - frameHeight) / 2)
        frame = pad + frame + pad
    clear()
    return frame


# Clear screen
def clear():
    # no idea how this works but it does
    print("\033c")


# Terminal dimensions [height, width]
def getTermDimensions():
    try:
        dimensions = subprocess.check_output(['stty', 'size']).split()
        return list(map(int, dimensions))
    except subprocess.CalledProcessError:
        return [DEFAULT_HEIGHT, DEFAULT_WIDTH]


class CountdownTimer:
    def __init__(self, initial_seconds):
        self.initial_seconds = initial_seconds
        self.remaining_seconds = initial_seconds
        self.running = False
        self.thread = None

    def start_pause(self):
        self.running = not self.running
        if self.running:
            self.thread = threading.Thread(target=self.countdown)
            self.thread.start()

    def countdown(self):
        while self.remaining_seconds > 0 and self.running:
            # print("\033c")
            # minutes = self.remaining_seconds // 60
            # seconds = self.remaining_seconds % 60
            # print(f"{minutes:02}:{seconds:02}")

            t = "%02s:%02d" % divmod(self.remaining_seconds, 60)
            print(center(asciiFormat(t, font), getTermDimensions()), end="")
            
            self.remaining_seconds -= 1
            time.sleep(1)
        if self.remaining_seconds > 0 and not self.running:
            print("Countdown paused!")
        else:
            print("Countdown finished!")

    def reset(self):
        self.running = False  
        self.remaining_seconds = self.initial_seconds
        
    def end(self):
        self.running = False  
        self.remaining_seconds = 0

# Example usage
timer = CountdownTimer(seconds)  # Create a 25-minute timer
with open(fontFile, "r") as f:
    font = f.read().split("\n<---->\n")
    font = [symbol.split("\n") for symbol in font]
old_settings = termios.tcgetattr(sys.stdin)  # Store original terminal settings

try:
    tty.setcbreak(sys.stdin.fileno())  # Put terminal in cbreak mode
    timer.start_pause()

    while True:
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            key = sys.stdin.read(1)
            if key == ' ': 
                timer.start_pause()
            elif key == 'r': 
                timer.reset()
                print("Timer reset!")
            elif key == 'q': 
                timer.end()
                print("Timer aborted!")
                break

finally:
    timer.end()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)  # Restore settings
