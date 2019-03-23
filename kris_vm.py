#!/usr/bin/env python3

'''

  ╔═════════════════════════════════════╗
  ║ KRIS ™ Computer Architecture Manual ║
  ╚═════════════════════════════════════╝


  Architecture: Benoit Sevens   - @benoitsevens  - https://b3n7s.github.io/
  Debugger/VM : Benjamin Evrard - @tsunulukai 🦆 - https://adelpha.be/


  The KRIS (acronym of "Kleine Ridikule Inefficiente Systeem") is an exotic,
  but sexy 8-bit computer architecture.



  0. Usage
  ════════
    Usage:
        kris_vm.py [options] [[-a] <program>]

    Options:
        -l <logfile>    Log file (defaults to computer.log)
        -d              Enable KRIS display at startup
        -a              Program file is in KRIS asm
        <program>       Program to load


    Example:
        ./kris_vm.py    helloworld.kris  -l helloworld.log -d
        ./kris_vm.py -a helloworld.krisa -l helloworld.log -d



  1. Registers
  ════════════

    There are 4 registers:

    ┌──────┬─────────────────────────────────────────────────────────────────┐
    │ REG1 │ General-Purpose Register 1                                      │
    │      │ Contains data that can be read from or written to memory        │
    │ REG2 │ General-Purpose Register 2                                      │
    │ PTR  │ Pointer                                                         │
    │      │ Contains a memory pointer where data can be read or written     │
    │ PC   │ Program Counter                                                 │
    │      │ Points to the next instruction to be executed                   │
    └──────┴─────────────────────────────────────────────────────────────────┘

    Each register is 8 bits long.



  2. Opcode reference table
  ═════════════════════════

    Each opcode is either 1 or 2 byte(s) long.

    For 1 byte long opcodes, the byte gets the value of the opcode.

    For 2 byte long opcodes:
    - The 1st byte gets the value of the opcode;
    - The 2nd byte gets the value of the argument.

    ┌───────────────────┬───────┬──────────────┬─────────────────────────────┐
    │ Mnemonic          │ Value │ instruction  │ Pseudocode                  │
    │                   │       │ size (bytes) │                             │
    ├───────────────────┼───────┼──────────────┼─────────────────────────────┤
    │ HALT              │ 0x0F  │ 1            │ Halts the CPU               │
    │ XOR               │ 0x10  │ 1            │ REG1 = REG1 ^ REG2          │
    │ ADD               │ 0x11  │ 1            │ REG1 = REG1 + REG2          │
    │ LOAD              │ 0x12  │ 1            │ REG1 = *PTR                 │
    │ STORE             │ 0x13  │ 1            │ *PTR = REG1                 │
    │ SET_PTR           │ 0x14  │ 1            │ PTR = REG1                  │
    │ SWAP              │ 0x15  │ 1            │ REG1 <-> REG2               │
    │                   │       │              │                             │
    │ SET_REG1 constant │ 0x20  │ 2            │ REG1 = constant             │
    │ JNZ constant      │ 0x21  │ 2            │ if REG1 != 0: goto constant │
    └───────────────────┴───────┴──────────────┴─────────────────────────────┘



  3. Memory layout
  ════════════════

    The computer has 256 bytes of RAM, which can be addressed with addresses
    ranging from 0 to 255.

    The computer program gets loaded (mapped) at address 0.

    There is a small screen attached to the computer which can display 16
    characters. This screen is memory mapped to the last 16 bytes of the RAM.
    Writing to this area of RAM (addresses 0xf0 - 0xff), displays a character
    on the corresponding position of the screen.



  4. Boot/Reset process
  ═════════════════════

    All registers (PC included) are initialised to 0 at boot or a reset.
    Execution starts at address 0.
    The Program Counter (PC) is automatically incremented with 1 or 2 bytes
    after each instruction, according to the length of the executed
    instruction.




  5. Debugger's commands
  ══════════════════════

    The debugger supports the following commands:

    ┌─────────────┬──────────────────────────────────────────────────────────────────┐
    │ Command     │ Description                                                      │
    ├─────────────┼──────────────────────────────────────────────────────────────────┤
    │ (s)tep      │ Executes a single instruction; it's the default command          │
    │ (r)un       │ Executes instructions until interrupted by user/breakpoint       │
    │ (a)ddbp     │ Adds an execution breakpoint at an address of your choice        │
    │ (d)elbp     │ Removes a breakpoint                                             │
    │ (l)og       │ Displays the last n lines of the status/trace log                │
    │ (m)an       │ Displays the current manual                                      │
    │ (q)uit      │ Exits the debugger                                               │
    │ (c)lear     │ Clears and refreshes the screen                                  │
    │ (C)lock     │ Change the CPU clock speed                                       │
    │ (D)isplay   │ Toggles the KRIS display (hex/ascii views)                       │
    │ (L)oad      │ Loads a program from disk                                        │
    │ (P)rogram   │ Enters programming mode; allows you to edit memory content       │
    │ (A)ssemble  │ Enters assembly mode; allows you to input KRIS ASM instructions  │
    │             │ In this mode, you can use the keyword 'address_xxh:' to indicate │
    │             │ at which offset your assembly bloc begins                        │
    │ (R)eset     │ Resets the KRIS computer                                         │
    │ (S)ave      │ Saves a program to disk until specified memory address           │
    │ (E)dit      │ Edits a Register/Memory value                                    │
    └─────────────┴──────────────────────────────────────────────────────────────────┘

'''

__description__ = 'Compatible KRIS ™ ("Kleine Ridikule Inefficiente Systeem") Debugger/Emulator'
__author__      = 'Benjamin Evrard, based on KRIS ™ Computer Architecture by Benoit Sevens'


from kris_ui import *
import docopt
import os
import pydoc
import re
import signal
import sys
import threading
import time


# UI configuration
title = "Compatible KRIS ™ Computer Emulator"
boxes = {
    "title":        {"tl": { "x":  1, "y":  1 }, "br": { "x": 59, "y":  3 }, "title_": "Compatible KRIS ™ Computer Emulator", "ct": C["F"]["L"]["RED"], "align": "center"},
    "memory":       {"tl": { "x":  1, "y":  4 }, "br": { "x": 59, "y": 23 }, "title": "Memory"},
    "registers":    {"tl": { "x": 60, "y":  4 }, "br": { "x": 80, "y":  9 }, "title": "Registers"},
    "disassembly":  {"tl": { "x": 60, "y": 10 }, "br": { "x": 80, "y": 23 }, "title": "Disassembly"},
    "clock":        {"tl": { "x": 60, "y":  1 }, "br": { "x": 80, "y":  3 }, "title": "Clock"},
    "display":      {"tl": { "x":  1, "y": 24 }, "br": { "x": 59, "y": 26 }, "title": "Display", "ct":C["F"]["L"]["RED"]},
    "cpuclock":     {"tl": { "x": 60, "y": 24 }, "br": { "x": 80, "y": 26 }, "title": "CPU Freq"},
    "console":      {"tl": { "x":  1, "y": 27 }, "br": { "x": 59, "y": 29 }, "title": "Console"},
    "losttime":     {"tl": { "x": 60, "y": 27 }, "br": { "x": 80, "y": 29 }, "title": "Time Lost"},
    "status":       {"tl": { "x":  1, "y": 30 }, "br": { "x": 80, "y": 35 }, "title": "Status"},
    "statuso":      {"tl": { "x":  1, "y": 33 }, "br": { "x": 80, "y": 35 }, "title_": "Status Overlay", "hidden": True},
    "breakpoints":  {"tl": { "x":  1, "y": 36 }, "br": { "x": 80, "y": 40 }, "title": "BreakPoints"},
    "breakpoints1": {"tl": { "x":  1, "y": 36 }, "br": { "x": 20, "y": 40 }, "hidden": True},
    "breakpoints2": {"tl": { "x": 20, "y": 36 }, "br": { "x": 40, "y": 40 }, "hidden": True},
    "breakpoints3": {"tl": { "x": 40, "y": 36 }, "br": { "x": 60, "y": 40 }, "hidden": True},
    "breakpoints4": {"tl": { "x": 60, "y": 36 }, "br": { "x": 80, "y": 40 }, "hidden": True},
    "validcmd":     {"tl": { "x":  1, "y": 41 }, "br": { "x": 80, "y": 41 }, "ct": C["R"], "title": " {0}H{1}elp{2} {0}s{1}tep{2} {0}r{1}un{2} {0}a{1}ddbp{2} {0}d{1}elbp{2} {0}l{1}og{2} {0}C{1}lock{2} {0}L{1}oad{2} {0}S{1}ave{2} {0}E{1}dit{2} {0}P{1}rogram{2} {0}A{1}SM{2} {0}R{1}eset{2} {0}Q{1}uit{2} ".format(C["B"]["D"]["RED"]+C["F"]["L"]["YEL"]+C["A"]["S"]["U"],C["F"]["D"]["BLK"]+C["B"]["D"]["CYA"]+C["A"]["R"]["U"], C["R"]), "cl": C["F"]["D"]["BLK"]},
}

# Cursor positions
cur_posn = {
    "exit" : {
        "x": 1,
        "y": 42
    },
    "prompt" : {
        "x": boxes["console"]["tl"]["x"]+2,
        "y": boxes["console"]["tl"]["y"]+1,
    },
    "PC" : {
        "x": boxes["disassembly"]["tl"]["x"]+1,
        "y": boxes["disassembly"]["tl"]["y"]+1,
    }
}

# Color definitions
CWRITE      = C["F"]["L"]["RED"]
CREAD       = C["F"]["L"]["CYA"]
CREADWRITE  = C["F"]["L"]["PUR"]
CEDIT       = C["B"]["D"]["CYA"] + C["F"]["D"]["BLK"]
CPC         = C["F"]["L"]["YEL"]
COPC        = C["F"]["D"]["GRY"]
CBP         = C["B"]["D"]["RED"]
CHDRHEX     = C["R"]


# VM Opcodes
OC = {
    "HLT"      : 0x0F,  # HALTS THE CPU
    "XOR"      : 0x10,  # R1 = R1 ^ R2
    "ADD"      : 0x11,  # R1 = R1 + R2
    "LOAD"     : 0x12,  # R1 = *PTR
    "STORE"    : 0x13,  # *PTR = R1
    "SET_PTR"  : 0x14,  # PTR = R1
    "SWAP"     : 0x15,  # R1 <-> R2
    "SET_R1"   : 0x20,  # R1 = arg;
    "JNZ"      : 0x21   # JMP NOT ZERO to arg
}

# VM Clock Speed
CLK = 100

# VM Registers
r = {
    "OPC": -1,
    "PC" : 0,
    "PTR": 0,
    "R1" : 0,
    "R2" : 0,
}

# VM Memory
memory = b"\x00" * 0x100

# VM Memory Operations State
vm_opr = {
    "memory" : {
        "r" : -1,
        "w" : -1,
        "x" : -1,
        "p" : -1,
    },
    "registers" : {
        "PC"  : -1,
        "PTR" : -1,
        "R1"  : -1,
        "R2"  : -1,
    }
}


# Debugger Configuration
view_disp_hex    = False        # Disable the view on the memory segment containing the computer display
view_disp_ascii  = False        # Disable the computer display
exit             = False        # Used as signal for thread termination when leaving the debugger
halt             = False        # Used as signal to stop the CPU when the corresponding instruction is hit
step             = True         # Used as signal to enable stepping mode
clock_tick       = False        # Used as signal to enable redrawing of screen parts during user input
refresh_ui_lines = False

# Debugger Initialization
status_hist = [" "]             # Log file
breakpoints = [ -1 ] * 12       # Breakpoints
clear_clk   = 0                 # Counter used to completely refresh the screen periodically
console     = "> "              # Default prompt
program     = {                 # Default program
    "name": "",
    "content" : "",
}



def get_asm(opcode):
    for k in OC:
        if OC[k] == opcode:
            return k
    return "DB[%02x]" % opcode


def get_ascii_print(b):
    retv = ""
    if b in range(0x20, 0x7f):
        return chr(b)
    else:
        #return "ⁿₐ"
        return "¿"


def clock():
    global refresh_ui_lines
    while not exit:
        while clock_tick and not exit:
            if ((time.time() - starttime) % 5) == 0:
                clear()
                refresh_ui_lines = True
                refresh_gui()
            else:
                cur_sav()
                refresh_clock()
                cur_res()
                time.sleep(1)
        time.sleep(.5)


def uinput(s=""):
    global clock_tick
    global console
    global cur_posn
    global clear_clk
    global boxes
    console = s
    draw_box_content(dump_console(),boxes["console"])
    cur_posn["prompt"]["x"] = boxes["console"]["tl"]["x"] + 3 + len(s)
    cur_set(cur_posn["prompt"]["x"], cur_posn["prompt"]["y"])
    clock_tick = True
    retv = input()
    clock_tick = False
    cur_set(cur_posn["prompt"]["x"], cur_posn["prompt"]["y"])
    clear_clk += 1
    if not (clear_clk % 10):
        #clear()
        draw_ui(boxes)
        refresh_gui()
    return retv


def refresh_gui(con=True):
    global refresh_ui_lines
    if refresh_ui_lines:
        draw_ui(boxes)
        refresh_ui_lines = False
    draw_box_content(title,boxes["title"], a="center", c=C["F"]["L"]["RED"])
    draw_box_content(dump_time(icon=True),boxes["clock"], a="center")
    draw_box_content(dump_memory(),boxes["memory"])
    draw_box_content(dump_registers(),boxes["registers"])
    draw_box_content(dump_disass(),boxes["disassembly"])
    cur_set(cur_posn["PC"]["x"],cur_posn["PC"]["y"])
    stdo_wf("%s⮞%s" % (C["F"]["L"]["RED"], C["R"]))
    cur_set(cur_posn["PC"]["x"]+content_w(boxes["disassembly"])+1,cur_posn["PC"]["y"])
    stdo_wf("%s⮜%s" % (C["F"]["L"]["RED"], C["R"]))
    draw_box_content(dump_display(),boxes["display"])
    draw_box_content(dump_clockspeed(),boxes["cpuclock"], a="center")
    draw_box_content(dump_run_time(),boxes["losttime"], a="center")
    draw_box_content(dump_status(),boxes["status"])
    draw_box_content("\n".join(dump_breakpoints().split("\n")[0:3]),boxes["breakpoints1"])
    draw_box_content("\n".join(dump_breakpoints().split("\n")[3:6]),boxes["breakpoints2"])
    draw_box_content("\n".join(dump_breakpoints().split("\n")[6:9]),boxes["breakpoints3"])
    draw_box_content("\n".join(dump_breakpoints().split("\n")[9:12]),boxes["breakpoints4"])
    draw_box_content(dump_validcmd(),boxes["validcmd"])
    if con:
        draw_box_content(dump_console(),boxes["console"])


def clear(lines=cur_posn["exit"]["y"], s = False):      # Clears the screen
    global boxes
    if s == False:                                      # Use custom clear routine (clears all but the console prompt line)
        for i in range (lines):
            cur_set(1, 1+i)
            if boxes["console"]["tl"]["y"] != i:
                prn(" ".ljust(100))
    else:                                               # Use system clear routine
        os.system("clear")


def refresh_clock():
    draw_box_content(dump_time(icon=True),boxes["clock"], a="center")
    draw_box_content(dump_run_time(),boxes["losttime"], a="center")


def read_f_keys():
    while True:
        time.sleep(.5)


def info(t, s=""):
    status_hist.append("%s %s%s: %s%s" % (dump_run_time(), C["F"]["L"]["CYA"], t.ljust(8), s, C["R"]))


def error(t, s=""):
    status_hist.append("%s %s%s: %s%s" % (dump_run_time(), C["F"]["L"]["RED"], t.ljust(8), s, C["R"]))


def warning(t, s=""):
    status_hist.append("%s %s%s: %s%s" % (dump_run_time(), C["F"]["L"]["YEL"], t.ljust(8), s, C["R"]))


def dump_console():
    return console


def dump_status():
    retv = ""
    lines = reversed(status_hist)
    for line in lines:
        retv += line[6:] + "\n"
    return retv


def dump_memory():
    retv = CHDRHEX + "  🦆 │"
    hexvalues = ""
    for i in range(0x10):
        retv +=" %02x" % i
        if i % 16 == 0x7:
            retv +=" "
    retv += C["R"] + "\n"
    retv += "─"*5 + "┼" + "─"*49 + "\n"
    for i in range(len(memory)):
        c = ""
        if i in breakpoints:
            c = CBP
        if i == vm_opr["memory"]["r"]:
            c += CREAD
        if i == vm_opr["memory"]["w"]:
            c += CWRITE
        if i == r["OPC"]:
            c += COPC
        if i == r["PC"]:
            c += CPC
        if i == vm_opr["memory"]["p"]:
            c += CEDIT
        if i in range(0xf0,0x100) and not view_disp_hex:
            hexvalues += " %s??%s" % (c+C["F"]["L"]["RED"], C["R"])
        else:
            hexvalues += " %s%02x%s" % (c, memory[i], C["R"])
        if i % 16 == 0x7:
            hexvalues += " "
        if i % 16 == 0xf:
            retv += "0x%02x │%s\n" % (i & 0xfffffff0, hexvalues)
            hexvalues = ""
            asciivalues = ""
            labels = ""
        elif i == len(memory)-1:
            if i%16 < 7: hexvalues += " "
            hexvalues += "   " *(15-i%16)
            asciivalues += " " *(15-i%16)
            retv += "0x%02x:  %s\n" % (i & 0xfffffff0, hexvalues)
    return retv


def dump_registers():
    retv = ""
    for reg, val in sorted(r.items()):
        if view_disp_ascii and reg not in ["PC", "PTR"]:
            s = " (%s)" % get_ascii_print(val)
        else:
            s = ""
        if reg != "OPC":
            if vm_opr["registers"][reg] == "w" :
                c = CWRITE
            elif vm_opr["registers"][reg] == "r" :
                c = CREAD
            elif vm_opr["registers"][reg] == "rw" :
                c = CREADWRITE
                s = "%s ⮌" % (s)
            elif vm_opr["registers"][reg] == "swap" :
                c = CREADWRITE
                s = "%s ⮂" % (s)
            else:
                c = C["R"]
            retv += "%s%-*s: 0x%02x%s%s\n" % (c, 4, reg, val, s, C["R"])
    return retv


def dump_disass():
    retv = ""
    opc = r["OPC"]
    pc = r["PC"]

    if opc == -1 :
        if cur_posn["PC"]["y"] != boxes["disassembly"]["tl"]["y"]+1:
            cur_posn["PC"]["y"] = boxes["disassembly"]["tl"]["y"]+1
            clear_content(boxes["disassembly"])
    if opc != -1 :
        if cur_posn["PC"]["y"] != boxes["disassembly"]["tl"]["y"]+2:
            cur_posn["PC"]["y"] = boxes["disassembly"]["tl"]["y"]+2
            clear_content(boxes["disassembly"])
        c = COPC
        retv += "%s0x%02x: " % (c, opc)
        retv += "%s" % get_asm(memory[opc])   # Instruction

        OC = memory[opc]
        if (OC >> 4) == 2:            # If Arg
            retv += " 0x%02x" % memory[opc+1] # Arg
        retv += "%s\n" %C["R"]

    for i in range(content_h(boxes["disassembly"])+1):
        if pc in range(len(memory)):
            c = ""
            if i == 0:
                c = CPC
            retv += "%s0x%02x: " % (c,pc)         # PC
            #retv += "%02x " % memory[pc]         # OPCODE
            retv += "%s" % get_asm(memory[pc])    # Instruction

            OC = memory[pc]
            if (OC >> 4) == 2:            # If Arg
                retv += " 0x%02x" % memory[pc+1]  # Arg

            retv += "%s\n" %C["R"]
            if memory[pc] >> 4 != 0:
                pc += memory[pc] >> 4
            else:
                pc += 1
        else:
            clear_content(boxes["disassembly"])
    return retv


def dump_display():
    if view_disp_ascii:
        return " " + memory[0xf0:].decode("ascii")
    else:
        return "<DISABLED>"


def dump_clockspeed():
    return "%s Hz" % (CLK)


def dump_breakpoints():
    retv = ""
    for i in range(len(breakpoints)):
        bpval = "Not set"
        if breakpoints[i] != -1:
            bpval = "0x%02x" % breakpoints[i]
        retv += "%02d. %s" % (i+1, bpval)
        retv += "\n"
    return retv


def dump_validcmd():
    retv = "{0}s{1}tep {0}r{1}un {0}a{1}dd_bp {0}d{1}el_bp {0}l{1}og {0}m{1}an {0}q{1}uit {0}C{1}lock {0}L{1}oad {0}P{1}rogram {0}R{1}eset {0}S{1}ave {0}U{1}pdt_reg".format(C["A"]["S"]["U"],C["A"]["R"]["U"])
    return retv


def update_memory(addr, val, silent=False):
    global memory
    memory = list(memory)
    memory[addr] = val
    memory = bytes(memory)
    if not silent:
        vm_opr["memory"]["w"] = addr


def add_breakpoint():
    ctx = "BP_ADD"
    err, addr = input_8bit(ctx, "Enter BreakPoint Address: ", "Address")
    if not err:
        if addr not in breakpoints:
            for i in range(len(breakpoints)):
                if breakpoints[i] == -1:
                    breakpoints[i] = addr
                    info(ctx, "Added Breakpoint %d at address 0x%02x" % (i+1,addr))
                    break
        else:
            warning(ctx, "Breakpoint at address 0x%02x was already set" % addr)


def del_breakpoint():
    ctx = "BP_DEL"
    n = uinput("Enter BreakPoint Number:")
    if n == "*":
        for i in range(len(breakpoints)):
            breakpoints[i] = -1
        info(ctx, "Deleted all breakpoints")
        return
    try:
        n = int(n) -1
        if n in range(10):
            if breakpoints[n] != -1:
                info(ctx, "Deleted Breakpoint %d at address 0x%02x" % (n+1, breakpoints[n]))
                breakpoints[n] = -1
            else:
                warning(ctx, "%d not set" % (n+1))
        else:
            error(ctx, "%d out of range" % (n+1))
    except ValueError:
        error(ctx, "Invalid Input")


def input_8bit(ctx, prompt, type="Value", val = False):
    if not val:
        val = uinput("%s: %s" % (ctx,prompt))
    #info(ctx, "Testing Value " + val)
    try :
        val = int(val,16)
        #info(ctx, "0x%02x is int" % val)
        if val == val & 0xff:
            #info(ctx, "0x%02x is 8 bits" % val)
            return 0, val
        else:
            error(ctx,"%s '0x%02x' out of range" % (type, val))
            return 1, 0
    except:
        if val == "q":
            return 2, 0
        error(ctx, "Invalid %s '%s'" % (type,val))
        return 1, 0


def exec():
    global r
    global memory
    global step
    global halt

    r["OPC"] = r["PC"]
    opcode = memory[r["PC"]]
    arg = memory[r["PC"]+1]
    instr = get_asm(opcode)

    for i in list(vm_opr):
        for j in list(vm_opr[i]):
            vm_opr[i][j] = -1

    if instr == "XOR":
        info(instr, "R1    = 0x%02x (R1) ^ 0x%02x (R2) = 0x%02x" % (r["R1"], r["R2"], r["R1"]^r["R2"]))
        r["R1"] ^= r["R2"]
        vm_opr["registers"]["R1"] = "rw"
        vm_opr["registers"]["R2"] = "r"

    if instr == "ADD":
        info(instr, "R1    = 0x%02x (R1) + 0x%02x (R2) = 0x%02x" % (r["R1"], r["R2"], r["R1"]+r["R2"]))
        r["R1"] += r["R2"]
        r["R1"] &= 0xff
        vm_opr["registers"]["R1"] = "rw"
        vm_opr["registers"]["R2"] = "r"

    if instr == "LOAD":
        r["R1"] = memory[r["PTR"]]
        info(instr, "R1    = *0x%02x = 0x%02x" % (r["PTR"],memory[r["PTR"]]))

        vm_opr["registers"]["R1"] = "w"
        vm_opr["memory"]["r"] = r["PTR"]

    if instr == "STORE":
        info(instr, "*0x%02x = 0x%02x" % (r["PTR"],r["R1"]))
        memory = list(memory)
        memory[r["PTR"]] = r["R1"]
        memory = bytes(memory)

        vm_opr["registers"]["R1"] = "r"
        vm_opr["memory"]["w"] = r["PTR"]

    if instr == "SET_PTR":
        r["PTR"] = r["R1"]
        info(instr, "PTR   = 0x%02x" % (r["R1"]))
        vm_opr["registers"]["R1"] = "r"
        vm_opr["registers"]["PTR"] = "w"

    if instr == "SWAP":
        info(instr, "R1    = 0x%02x ; R2 = 0x%02x" % (r["R2"], r["R1"]))
        t = r["R1"]
        r["R1"] = r["R2"]
        r["R2"] = t
        vm_opr["registers"]["R1"] = "swap"
        vm_opr["registers"]["R2"] = "swap"

    if instr == "SET_R1":
        r["R1"] = arg
        info(instr, "R1    = 0x%02x (imm)" % (arg))
        vm_opr["registers"]["R1"] = "w"
        vm_opr["memory"]["r"] = r["PC"]+1

    if instr == "HLT":
        step = True
        halt = True
        warning(instr, "System Halted!")

    if "DB[" in instr:
        step = True
        error(instr, "Invalid instruction!")

    # Set PC for next instruction
    if instr == "JNZ" and r["R1"] != 0 :
        ni = memory[r["PC"]+1]
        info(instr, "PC    = 0x%02x (Jump taken)" % (ni))
        if ni == r["PC"]:
            warning(instr, "Inifinite Jump loop at 0x%02x, System Halted!" % (ni))
            halt = True
        vm_opr["registers"]["PC"] = "w"
    elif instr == "JNZ":
        ni = r["PC"] + (opcode >> 4)
        info(instr, "PC    = 0x%02x (Jump NOT taken)" % (ni))
    elif instr == "HLT":
        ni = r["PC"]
    else:
        ni = r["PC"] + (opcode >> 4)
    r["PC"] = ni
    ni = ""


def run():
    refresh_gui()
    exec()
    while not step and not halt and r["PC"] not in breakpoints:
        brkmsg = "Running; Press CTRL+C to Interrupt..."
        refresh_clock()
        refresh_gui()
        draw_box_content("%s%s%s" % (C["F"]["L"]["YEL"], brkmsg.ljust(content_w(boxes["status"])), C["R"]), boxes["statuso"])
        exec()
        time.sleep(1/CLK)
    if r["PC"] in breakpoints:
        warning("INT", "Hit Breakpoint %d at address 0x%02x" % (breakpoints.index(r["PC"]) + 1,r["PC"]))


def reset():
    ctx = "STATUS"
    global r
    global memory
    global vm_opr
    global halt
    global step

    memory = b"\x00" * 0x100

    if len(status_hist) <= 1 :
        info(ctx, "Initializing computer")
    else:
        info(ctx, "Reinitializing computer")

    r = {
        "OPC": -1,
        "PC" : 0,
        "PTR": 0,
        "R1" : 0,
        "R2" : 0,
    }

    vm_opr = {
        "memory" : {
            "r" : -1,
            "w" : -1,
            "x" : -1,
            "p" : -1,
        },
        "registers" : {
            "PC"  : -1,
            "PTR" : -1,
            "R1"  : -1,
            "R2"  : -1,
        }
    }

    refresh_gui()
    time.sleep(.5)

    if program["content"]:
        info("LOAD", "Loading program '%s'" % program["name"])

        for i in range(len(program["content"])):
            update_memory(i, program["content"][i])
            refresh_gui()
            time.sleep(1/CLK)

        vm_opr["memory"]["w"] = -1

    halt = False
    step = True

    info(ctx, "Ready")


def load(prog):
    global program
    ctx = "LOAD"
    if os.path.isfile(prog):
        try:
            f = open(prog, "rb")
            program["name"] = prog
            program["content"] = f.read()
            f.close()
            return True
        except:
            error(ctx, "Can't read file '%s'" % prog)
            return False
    else:
        error(ctx, "File '%s' not found" % prog)
        return False


def load_asm(asm):
    global program
    ctx = "ASM"

    if os.path.isfile(asm):
        try:
            program["name"] = asm.replace(".kris", "", -1)
            f = open(asm, "r")
            info("ASM", "Loading program source code '%s'" % asm)
            for line in f.read().split("\n"):
                assemble(line)
                refresh_gui()
                time.sleep(1/CLK)
            ptr = vm_opr["memory"]["p"]
            vm_opr["memory"]["p"] = -1
            info("ASM", "Source code '%s' loaded" % asm)
            refresh_gui()
            program["content"] = memory[:ptr]
            f.close()
            return True
        except:
            error(ctx, "Can't read file '%s'" % asm)
            return False
    else:
        error(ctx, "File '%s' not found" % asm)
        return False


def cmd_display_toggle():
    ctx = "STATUS"
    global view_disp_ascii
    global view_disp_hex
    global boxes
    if view_disp_ascii:
        view_disp_ascii = False
        view_disp_hex = False
        boxes["display"]["ct"] = C["F"]["L"]["RED"]
        info(ctx, "Display deactivated - ASCII/Hex views")
        #info(ctx, "No more hints available, didn't you lose enough points ?!?")
    elif view_disp_hex:
        view_disp_ascii = True
        del boxes["display"]["ct"]
        #info(ctx, "Display Activated; 5 Points lost")
        info(ctx, "Display activated - ASCII view")
    else:
        view_disp_hex = True
        #info(ctx, "HexView Activated; 5 Points lost")
        info(ctx, "Display activated - Hex view")


def cmd_log():
    global refresh_ui_lines
    ctx = "LOG"
    n = uinput("Number of previous log lines to display:")
    clear(s=True)
    try:
        n = int(n)
        info(ctx, "Displaying last %s status lines" % n)
    except:
        n = ""
        info(ctx, "Displaying complete status lines log")
    if n == "":
        pydoc.ttypager("\n ".join(status_hist))
    else:
        pydoc.ttypager("\n ".join(status_hist[-n:]))
    input("\n\nEnd of log file; Press <ENTER> to continue")
    clear(s=True)
    refresh_ui_lines = True


def cmd_load():
    ctx = "LOAD"
    format = ""
    while format.lower() not in ["b", "s", "q"]:
        format = uinput("Load (B)inary of (S)ource code ?")
    prog = uinput("Enter filename:")
    if format.lower() == "b":
        if load(prog):
            reset()
    elif format.lower() == "s":
        if os.path.isfile(prog):
            program["content"] = False
            reset()
            load_asm(prog)
        else:
            error(ctx, "File '%s' not found" % prog)


def cmd_save():
    ctx = "SAVE"
    err, addr = input_8bit(ctx, "Save mode - End offset ?", "Address")
    if addr == "q":
        pass
    elif addr :
        fn = uinput("Save mode - Filename ?")
        f = ""
        try:
            f = open(fn, "xb")
            f.write(memory[:addr+1])
            info(ctx, "Program saved to file as '%s' (Memory 0x00-0x%02x)" % (fn,addr))
        except FileExistsError:
            error(ctx, "File already exists")
        except:
            error(ctx, "Can't open file")
        if f:
           f.close()
        info(ctx, "Leaving save mode")


def cmd_edit():
    ctx = "EDIT"
    reg = uinput("Which register do you want to update ?")
    if reg in list(r):
        err, val = input_8bit(ctx, "New value for register %s:" % reg)
        if not err:
            r[reg] = val
            info(ctx, "%s = 0x%02x" % (reg, val))
    elif reg == "M":
        err, addr = input_8bit(ctx, "Which memory address do you want to update ?", "Address")
        if not err:
            err, val = input_8bit(ctx, "New value for memory address 0x%02x:" % addr)
            if not err:
                update_memory(addr, val)
                info(ctx, "*0x%02x = 0x%02x" % (addr, val))
    else:
        error(ctx, "Invalid Register '%s'" % reg)


def cmd_prog():
    ctx = "PROG"
    info(ctx, "Entering programming mode")
    refresh_gui()
    err, addr = input_8bit(ctx, "Program mode - Start offset ?", "Memory Address")
    if not err:
        vm_opr["memory"]["p"] = addr
        refresh_gui()
        val = ""
        while err != 2 :
            err, val = input_8bit(ctx, "Program mode - 0x%02x:" % addr)
            if not err:
                update_memory(addr, val)
                info(ctx, "*0x%02x = 0x%02x" % (addr, val))
                addr += 1
                vm_opr["memory"]["p"] = addr
            refresh_gui()
            if addr != addr & 0xff:
                warning(ctx, "Reached end of memory space")
                err = 2
        info(ctx, "Leaving programming mode")
        refresh_gui()
        vm_opr["memory"]["p"] = -1


def cmd_assemble():
    global refresh_ui_lines
    global r
    vm_opr["memory"]["p"] = r["PC"]
    ctx = "ASM"
    info(ctx, "Entering Assembly mode")
    refresh_gui()
    cmd = ""
    while cmd != "q":
        if vm_opr["memory"]["p"] == vm_opr["memory"]["p"] & 0xff:
            cmd = uinput("%s: Enter Assembly Instruction:" % ctx)
            assemble(cmd)
            refresh_gui()
        else:
            warning(ctx, "Reached end of memory space")
            break
    info(ctx, "Leaving Assembly Mode")
    vm_opr["memory"]["p"] = -1
    refresh_ui_lines=True
    refresh_gui()


def assemble(cmd):
    cmd = cmd.lstrip().rstrip().replace("SET_REG1", "SET_R1")
    if cmd:
        ctx = "ASM"
        match = False
        infostr =  "*0x%02x: " % vm_opr["memory"]["p"]
        for opcode in OC.keys():
            if cmd.startswith(opcode):
                match = True
                if OC[opcode] >> 4 == 2:
                    if (vm_opr["memory"]["p"]+1) == (vm_opr["memory"]["p"]+1) & 0xff:
                        arg = cmd.replace(opcode, "").lstrip()
                        try:
                            argval = int(arg,16)
                            if argval == argval & 0xff:
                                infostr += "%-15s=> '0x%02x%02x'"  % (("'" + opcode + " " + arg + "'"),OC[opcode], argval)
                                info(ctx,  infostr)
                                update_memory(vm_opr["memory"]["p"], OC[opcode])
                                update_memory(vm_opr["memory"]["p"]+1, argval)
                                vm_opr["memory"]["p"] +=2
                            else:
                                error(ctx,"%s argument '0x%02x' out of range" % (opcode, argval))
                        except:
                            error(ctx, "Invalid argument provided for '%s' instruction" % opcode)
                    else:
                        error(ctx, "Not enough memory space available for a 2 bytes instruction")
                else:
                    infostr += "%-15s=> '0x%02x'"  % ("'"+opcode+"'",OC[opcode])
                    info(ctx,  infostr)
                    update_memory(vm_opr["memory"]["p"], OC[opcode])
                    vm_opr["memory"]["p"] +=1
        if cmd.startswith("address_") and cmd.endswith("h:"):
            match = True
            #address = int(cmd.replace("address_","").replace("h:", ""),16)
            err, addr = input_8bit(ctx, "", type="Address", val = cmd.replace("address_","").replace("h:", ""))
            if not err:
                info(ctx, "Address 0x%02x" % addr)
                vm_opr["memory"]["p"] = addr
        if cmd.startswith("#"):
            match = True
            info(ctx+"-C", "%s" % cmd)
        if not match:
            try:
                regmatch = re.findall("0x[0-9a-f]{1,2}", cmd)
                for m in regmatch:
                    cmd = int(m,16)
                    if cmd == cmd & 0xff:
                        infostr = "*0x%02x: 'DB[0x%02x]'     => '0x%02x'" % (vm_opr["memory"]["p"], cmd, cmd)
                        info(ctx,  infostr)
                        update_memory(vm_opr["memory"]["p"], cmd)
                        vm_opr["memory"]["p"] +=1
                        match = True
                else:
                    raise ValueError
            except:
                pass
        if not match:
                if cmd.lower() in ["h", "m", "help", "man", "?"] :
                    pydoc.pager(__doc__)
                elif cmd != "q":
                    error(ctx, "'%s' Invalid Instruction" % cmd)


def cmd_clock():
    global CLK
    ctx = "CLK"
    try:
        CLK = float(uinput("Enter the new clock speed:"))
        if CLK == int(CLK):
            CLK = int(CLK)
        info(ctx, "Clock speed adjusted to %4.2f Hz" % CLK)
    except:
        error(ctx, "Invalid value")


def cmd_quit(logfile):
    ctx = "STATUS"
    exit=True
    info(ctx, "Writing debugger's log to '%s'" % logfile)
    info(ctx, "Exiting debugger")
    try:
        f = open(logfile, "w").write("\n ".join(status_hist))
        f.close()
    except:
        pass
    refresh_gui()
    cur_set(cur_posn["exit"]["x"],cur_posn["exit"]["y"])
    sys.exit(0)


# Signal handling
def handler_SIGINT(sig, frame):
    global step
    global refresh_ui_lines
    warning("INT", "User Interruption")
    step = True
    refresh_ui_lines = True

def handler_SIGTSTP(sig, frame):
    return

def handler_SIGQUIT(sig, frame):
    return

signal.signal(signal.SIGINT,  handler_SIGINT)
signal.signal(signal.SIGTSTP, handler_SIGTSTP)
signal.signal(signal.SIGQUIT, handler_SIGQUIT)


def main():
    global step
    global halt
    global view_disp_ascii
    global view_disp_hex

    # Read command line arguments
    args = docopt.docopt(__doc__)


    if args["<program>"] and os.path.isfile(args["<program>"]) and not args["-a"]:
        load(args["<program>"])

    if args["-l"]:
        logfile = args["-l"]
    else:
        logfile = "computer.log"

    if not logfile.endswith(".log"):
        logfile += ".log"

    if args["-d"]:
        view_disp_hex = True
        view_disp_ascii = True
        del boxes["display"]["ct"]

    # Init GUI
    clear(s=True)
    draw_ui(boxes)
    refresh_gui()
    reset()
    fcmd = ""

    if args["<program>"] and args["-a"] and os.path.isfile(args["<program>"]):
        load_asm(args["<program>"])

    # Start thread to refresh clocks
    clk = threading.Thread(name= "clock", target=clock, daemon = True)
    clk.start()

    # Start thread to read Function Keys
    #rfk = threading.Thread(name= "read_f_keys", target=read_f_keys, daemon = True)
    #rfk.start()

    # Main loop
    while True:
        refresh_gui()
        cmd = uinput(">")

        if cmd == "":
            cmd = "s"

        if cmd.lower() in ["h", "m", "help", "man", "?"] :
            ctx = "HELP"
            info(ctx, "Displaying KRIS manual")
            pydoc.pager(__doc__)

        elif cmd == "s" or cmd.lower() == "step":
            ctx = "STEP"
            step = True
            info(ctx, "Executing 1 instruction")
            run()

        elif cmd == "r" or cmd.lower() == "run":
            ctx = "STATUS"
            info(ctx, "Running; press CTRL+C to interrupt")
            step = False
            halt = False
            run()

        elif cmd == "A":
            cmd_assemble()

        elif cmd == "a" or cmd.lower() in ["b", "addbp", "bp", "breakpoint"]:
            add_breakpoint()

        elif cmd == "d" or cmd.lower() in ["delbp"]:
            del_breakpoint()

        elif cmd == "D" or cmd.lower() == "display":
            cmd_display_toggle()

        elif cmd == "C" or cmd.lower() in ["clk", "clock"]:
            cmd_clock()

        elif cmd == "c" or cmd.lower() in ["clr", "clear"]:
            info("CLEAR", "Refreshing Screen")
            clear(s=True)
            draw_ui(boxes)
            refresh_gui()

        elif cmd == "l" or cmd.lower() in ["log","status"]:
            cmd_log()

        elif cmd == "L" or cmd.lower() == "load":
            cmd_load()

        elif cmd == "S" or cmd.lower() == "save":
            cmd_save()

        elif cmd.lower() in ["e", "edit", "editreg"]:
            cmd_edit()

        elif cmd.lower() in ["p", "prog", "program"]:
            cmd_prog()

        elif cmd == "R":
            while cmd != "Y" or cmd != "N":
                cmd = uinput("Are you SURE you want to Reset (Y/N) ?")
                if cmd.lower() == "y":
                    reset()
                    break
                if cmd.lower() == "n":
                    break

        elif cmd.lower() in [ "q", ":q", "quit","exit"]:
            while cmd != "Y" or cmd != "N":
                cmd = uinput("Are you SURE you want to Quit (Y/N) ?")
                if cmd.lower() == "y":
                    cmd_quit(logfile)
                    break
                if cmd.lower() == "n":
                    break

        elif cmd.lower() ==  "q!":
            cmd_quit(logfile)

        else:
            ctx = "CMD"
            error(ctx, "INVALID Command '%s'" % cmd)


if __name__ == "__main__":
    main()
