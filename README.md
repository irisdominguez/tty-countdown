# TTY-Countdown

![screenshot](http://i.imgur.com/lnRXPyZ.png)

A countdown timer that will live forever in the shadow of 
[tty-clock](https://github.com/xorg62/tty-clock).


## Usage
    usage: tty-countdown [-h] [-m MINUTES] [-s SECONDS] [-f FONT] [-n]
    
    Fancy countdown script
    
    optional arguments:
      -h, --help            show this help message and exit
      -m MINUTES, --minutes MINUTES
                            Number of minutes
      -s SECONDS, --seconds SECONDS
                            Number of seconds
      -f FONT, --font FONT  Custom font file
      -n, --nocenter        Do not center timer (more efficient)

    controls:
      Spacebar: pause / resume the timer
      q: quit the timer
      r: reset the timer
      
## Installation

    $ mkdir -p ~/.local/opt & mkdir -p ~/.local/bin
    $ git clone https://github.com/irisdominguez/tty-countdown ~/.local/opt/tty-countdown
    $ sudo ln -s ~/.local/opt/tty-countdown/tty-countdown.py ~/.local/bin/tty-countdown

### Windows
* Does this even work on Windows?
