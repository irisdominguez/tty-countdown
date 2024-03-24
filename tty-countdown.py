#!/usr/bin/python

import subprocess
import argparse
import time
import threading
import select
import tty
import termios
import sys
import os

try:
    import plyer
    sysNotify = True
except:
    print("Plyer not installed. System notifications not available")
    sysNotify = False


# Default dimensions just in case
DEFAULT_HEIGHT = 24
DEFAULT_WIDTH = 80

# Arguments
parser = argparse.ArgumentParser(description="Fancy countdown script")

parser.add_argument("-m", "--minutes", action="store",
                    type=int, help="Number of minutes",
                    default=0)
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

parser.add_argument("-d", "--disable-notification", action="store_true",
                    help="Do not emit a system notification when finished")

args = parser.parse_args()

centered = not args.nocenter
seconds = args.seconds
minutes = args.minutes
fontFile = args.font
if sysNotify:
    sysNotify = not args.disable_notification

seconds = minutes * 60 + seconds
# Default time to pomodoro (25 mins)
if seconds == 0:
    seconds = 25 * 60


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

        # If it doesn't fit, return None
        if (termWidth < frameWidth) or (termHeight < (frameHeight + 3)):
            return None
        
        # pad horizontally
        pad = " " * int((termWidth - frameWidth) / 2)
        frame = "\n".join([(pad + line + pad) for line in frame])

        # pad vertically
        pad = "\n" * int((termHeight - frameHeight) / 2)
        frame = pad + frame + pad
    else:
        frame += "\n\n"
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

def printTime(seconds, status, instructions):
    clear()
    t = "%02d:%02d" % divmod(max(seconds, 0), 60)
    frame = center(asciiFormat(t, font), getTermDimensions())
    if frame is None:
        print(t)
    else:
        print(frame, end="")
        print(status)
        print(instructions)

class CountdownTimer:
    def __init__(self, initial_seconds):
        self.initial_seconds = initial_seconds
        self.updatetime = 0.2
        self.remaining_seconds = initial_seconds + 1 - self.updatetime
        self.running = False
        self.thread = None
        self.status = "Initialize..."
        self.instructions = "space: start, q: quit, r: reset"

    def start_thread(self):
        if self.thread:
            return
        self.thread = threading.Thread(target=self.countdown)
        self.thread.start()        

    def start_pause(self):
        self.running = not self.running
        if self.running:
            self.start_thread()
            self.status = "Working..."
            self.instructions = "space: pause, q: quit, r: reset"
        else:
            self.status = "Paused..."
            self.instructions = "space: resume, q: quit, r: reset"
            self.print()

    def reset(self):
        self.remaining_seconds = self.initial_seconds + 1 - self.updatetime
        if self.running:
            self.print()
        else:
            print("We are stopped, trying to reset")
            self.running = False
            self.start_pause()
        
    def end(self):
        self.running = False
        self.status = "Aborted!"
        self.instructions = "Bye!"
        self.print()

    def notify(self):
        if sysNotify:
            plyer.notification.notify(
                title = "Timer finished",
                message = f"Your timer has finished",
                app_icon = '',
                timeout = 5,
            )

    def print(self):
        printTime(int(self.remaining_seconds),
                      self.status,
                      self.instructions)

    def countdown(self):
        while self.remaining_seconds >= 0 and self.running:
            self.print()
            time.sleep(self.updatetime)
            self.remaining_seconds -= self.updatetime
            if self.remaining_seconds <= 0:
                self.running = False
                self.status = "Finished!"
                self.instructions = "q: quit, r: reset"
                self.notify()
        else:
            self.print()
            self.thread = None

# Create the timer
timer = CountdownTimer(seconds)
# Load the font
with open(fontFile, "r") as f:
    font = f.read().split("\n<---->\n")
    font = [symbol.split("\n") for symbol in font]
old_settings = termios.tcgetattr(sys.stdin)  # Store original terminal settings

try:
    tty.setcbreak(sys.stdin.fileno())  # Put terminal in cbreak mode
    timer.start_pause() # start timer

    while True:
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            key = sys.stdin.read(1)
            if key == ' ': 
                timer.start_pause()
            elif key == 'r': 
                timer.reset()
            elif key == 'q': 
                timer.end()
                break

finally:
    timer.end()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)  # Restore settings
