#!/usr/bin/env python3

'''

Basic UI interface for KRIS VM
Author : Benjamin Evrard - @tsunulukai 🦆 - https://adelpha.be/

'''

__description__ = 'KRIS Debugger UI routines'
__author__      = 'Benjamin Evrard'

import datetime
import os
import sys
import time

starttime = time.time()


# ANSI Control Codes for Color/Style Control
C = {
    "F": {                          # FOREGROUND
        "D": {                      # DARK
            "BLK" : "\033[30m",     # Black
            "RED" : "\033[31m",     # Red
            "GRE" : "\033[32m",     # Green
            "YEL" : "\033[33m",     # Yellow
            "BLU" : "\033[34m",     # Blue
            "PUR" : "\033[35m",     # Purple
            "CYA" : "\033[36m",     # Cyan
            "GRY" : "\033[90m",     # Grey
            "WHI" : "\033[97m",     # White
        },
        "L": {                      # LIGHT
            "GRY" : "\033[37m",     # Grey
            "RED" : "\033[91m",     # Red
            "GRE" : "\033[92m",     # Green
            "YEL" : "\033[93m",     # Yellow
            "BLU" : "\033[94m",     # Blue
            "PUR" : "\033[95m",     # Purple
            "CYA" : "\033[96m",     # Cyan
            "WHI" : "\033[97m",     # White
        },
    },
    "B": {                          # BACKGROUND
        "D": {                      # DARK
            "BLK" : "\033[40m",     # Black
            "RED" : "\033[41m",     # Red
            "GRE" : "\033[42m",     # Green
            "YEL" : "\033[43m",     # Yellow
            "BLU" : "\033[44m",     # Blue
            "PUR" : "\033[45m",     # Purple
            "CYA" : "\033[46m",     # Cyan
            "GRY" : "\033[100m",    # Grey
            "WHI" : "\033[107m",    # White
        },
        "L": {                      # LIGHT
            "GRY" : "\033[47m",     # Grey
            "RED" : "\033[101m",    # Red
            "GRE" : "\033[102m",    # Green
            "YEL" : "\033[103m",    # Yellow
            "BLU" : "\033[104m",    # Blue
            "PUR" : "\033[105m",    # Purple
            "CYA" : "\033[106m",    # Cyan
            "WHI" : "\033[107m",    # White
        },
    },
    "A": {                          # ATTRIBUTE
        "S": {                      # SET
            "B" : "\033[1m",        # Bold
            "D" : "\033[2m",        # Dim
            "U" : "\033[4m",        # Underlined
            "L" : "\033[5m",        # Blink
            "R" : "\033[7m",        # Reverse
            "H" : "\033[8m",        # Hidden
        },
        "R": {                      # RESET
            "B" : "\033[21m",       # Bold
            "D" : "\033[22m",       # Dim
            "U" : "\033[24m",       # Underlined
            "L" : "\033[25m",       # Blink
            "R" : "\033[27m",       # Reverse
            "H" : "\033[28m",       # Hidden
            "A" : "\033[0m",        # ALL
        }
    },
    "R"     : "\033[0m",            # RESET ALL

}

CLOCK = {}
for h in range(0xc):
        hour  = "%02d" % (h+1)
        ucode = 0x1F550 + h                 
        CLOCK[ hour + "00"] = chr(ucode)      # 0x1F550 = 🕐 (01H00)
        CLOCK[ hour + "30"] = chr(ucode+12)   # 0x1F55c = 🕜 (01H30)
CLOCK ["0000"] = CLOCK ["1200"]
CLOCK ["0030"] = CLOCK ["1230"]


# Default Lines and Title Colors
C["LINE"]  = C["F"]["L"]["BLU"]
C["TITLE"] = C["F"]["L"]["GRE"]

# Default Cursor Positions
cur_posn = {
    "exit" : {
        "x":  1,
        "y": 41,
    },
    "prompt" : {
        "x":  1,
        "y":  1,
    },
}

boxes={}

def prn(s, end=""):
    #stdwf(s+end)
    print(s, end=end, flush=True)


def stdo_wf(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def cur_sav():                          # Saves the cursor position
    stdo_wf("\033[s")


def cur_res():                          # Restores the saved cursor position
    stdo_wf("\033[u")


def cur_set(x,y):                       # Sets the cursor position
    stdo_wf("\033[%d;%df" % (y,x))


def draw_line_h(x,y,l,p,c=C["LINE"]):   # Draws an horizontal line
    cur_set(x,y)
    if p == "t":
        dl = "┌"
        dr = "┐"
    elif p == "b":
        dl = "└"
        dr = "┘"
    else:
        dl = dr = "─"
    prn("%s%s%s%s%s" % (c,dl,"─"*(l-2),dr,C["R"]))


def draw_line_v(x,y,l,p,c=C["LINE"]):   # Draws an vertical line
    for i in range (l):
        cur_set(x,y+i)
        if i == 0 :
            if p == "l":
                d = "┌"
            elif p == "r":
                d = "┐"
        elif i == l-1:
            if p == "l":
                d = "└"
            elif p == "r":
                d="┘"
        else:
            d = "│"
        prn("%s%s%s" % (c,d,C["R"]))


def draw_square(box):                   # Draws a square from a box object
    x1 = box["tl"]["x"]
    x2 = box["br"]["x"]
    y1 = box["tl"]["y"]
    y2 = box["br"]["y"]
    c = C["LINE"]
    if "cl" in box:
        c = box["cl"]
    if y2 != y1:
        draw_line_h(x1, y1, (x2-x1)+1, "t", c)
        draw_line_h(x1, y2, (x2-x1)+1, "b", c)
        draw_line_v(x1, y1, (y2-y1)+1, "l", c)
        draw_line_v(x2, y1, (y2-y1)+1, "r", c)
    else:
        draw_line_h(x1, y1, (x2-x1)+1, "m", c)
    


def draw_ui(ui_boxes):                  # Draws an UI from a dictionary of box objects
    for name, box in ui_boxes.items():
        draw_box(box)


def draw_box(box):                      # Draws a box and its title from a box object
    if "hidden" not in box:
        draw_square(box)
    if "title" in box:
        c = C["TITLE"]
        if "to" in box:
            to = box["to"]
        else:
            to = 0
        
        if "ct" in box:
            c = box["ct"]
        cur_set(box["tl"]["x"]+2+to, box["tl"]["y"])
        if "align" not in box:
            str = "[%s%s%s]" % (c,box["title"],C["R"])
        else:
            if box["align"] == "center":
                str = "%s[%s]%s" % (c, box["title"].center(box["br"]["x"] - box["tl"]["x"]-5), C["R"])
        prn(str)


def draw_box_content(content, box, a="left", c=""):     # Prints contents into a box
    x = box["tl"]["x"] + 2
    y = box["tl"]["y"] + 1
    lx = content_w(box)
    ly = content_h(box)

    c_arr = content.split("\n")
    for i in range(len(c_arr)):
        if i <= ly:
            line = c_arr[i].rstrip("\n")
            if a == "left":
                print_box_line(x, y+i, lx, c+line)
            elif a == "center":
                # FIXME
                print_box_line(x, y+i, lx, c+line, "center")
                #cur_set(x-1, y+i)
                #prn(" " + c + line[:lx].center(content_w(box)) + C["R"] + " ", end="")


def print_box_line(x,y,lenght,content,align="left"): # Prints a line at a given position with a constrained lenght 
    cur_set(x-1, y)
    oversized = False
    if len(strip_acc(content)) > lenght:
        oversized = True
        align = "left"
    while len(strip_acc(content)) > lenght:
        content = content[:-1]
    padding = " " * (lenght-len(strip_acc(content))+1)
    if align == "left":
        prn(" %s%s%s" % (content[:lenght+acc_len(content)], padding, C["R"]), end="")
        if oversized:
            cur_set(x+lenght-1, y)
            prn("…")
    if align == "center":
        prn(content.center(lenght) + C["R"], end="")


def ansi_cc():                          # Returns a list of ANSI Control Codes
    retv = []
    retv += C["F"]["D"].values()
    retv += C["F"]["L"].values()
    retv += C["B"]["D"].values()
    retv += C["A"]["S"].values()
    retv += C["A"]["R"].values()
    return retv

def long_uchar():
    retv = []
    retv += "🦆"
    retv += CLOCK.values()
    return retv


def strip_acc(str):                     # Strips a string from ANSI Control Codes
    for cc in ansi_cc():
        str = str.replace(cc,"")
    for uc in long_uchar():
        str = str.replace(uc, "  ")
    return str


def acc_len(str):                       # Returns the size delta between a string and its ANSI Control Codes stripped counterpart
    return len(str)-len(strip_acc(str))


def clear_content(box):                 # Clears the content of a box object
    x = box["tl"]["x"] + 1
    y1 = box["tl"]["y"] + 1
    y2 = box["br"]["y"] + 1
    for i in range (y2-y1-1):
        cur_set(x, y1+i)
        prn(" " * (content_w(box)+2))


def content_w(box):                     # Returns the available width within a box object
    return box["br"]["x"] - box["tl"]["x"] - 3


def content_h(box):                     # Returns the available height within a box object
    return box["br"]["y"] - box["tl"]["y"] - 2


def clear(lines=cur_posn["exit"]["y"], s = False):      # Clears the screen
    global boxes
    if s == False:                                      # Use custom clear routine (clears all but the prompt)
        for i in range (lines):
            cur_set(1, 1+i)
            #if boxes["console"]["tl"]["y"] != i:       # BUGS because boxes is defined in the importing program
            prn(" ".ljust(100))
    else:                                               # Use system clear routine
        os.system("clear")


def dump_run_time():
    runtime = time.time() - starttime
    return ("%02d:%02d" % (runtime / 60, runtime % 60))


def dump_time(icon=True):
    now = datetime.datetime.now()
    if not icon:
        return ("%02d:%02d:%02d" % (now.hour, now.minute, now.second))
    else:
        nowclock = CLOCK["%02d%02d" % (now.hour%12, + int(30 * int(float(now.minute)/30))%60)]
        return ("%s %02d:%02d:%02d" % (nowclock, now.hour, now.minute, now.second))