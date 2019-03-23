## ----------------------------------------------------------------------
# KRIS bytecode processor module
# For Hex-Rays IDA PRO 7.1

import sys
import struct

from ida_bytes import *
from ida_ua import *
from ida_idp import *
from ida_auto import *
from ida_nalt import *
from ida_funcs import *
from ida_lines import *
#from ida_problems import *
from ida_segment import *
from ida_name import *
from ida_netnode import *
from ida_xref import *
from ida_idaapi import *
import ida_frame
import ida_offset
import idc

# ----------------------------------------------------------------------
class kris_processor_t(processor_t):

    # ----------------------------------------------------------------------
    def __init__(self):
        processor_t.__init__(self)
        self.PTRSZ = 1
        self.init_instructions()
        self.init_registers()

    # ----------------------------------------------------------------------
    id = 0x8FFFF
    flag = PR_SEGS | PRN_HEX | PR_RNAMESOK | PR_NO_SEGMOVE
    cnbits = 8
    dnbits = 8

    # short processor names
    # Each name should be shorter than 9 characters
    psnames = ['kris']
    plnames = ['KRIS 8-bit computer']
    segreg_size = 0
    instruc_start = 0
    tbyte_size = 0

    # only one assembler is supported
    assembler = {
        'flag' : ASH_HEXF3 | AS_UNEQU | AS_COLON | ASB_BINF4 | AS_N2CHR,
        'uflag' : 0,
        'name' : "KRIS assembler",
        'origin': "org",
        'end': "end",
        'cmnt': ";",
        'ascsep': "\"",
        'accsep': "'",
        'esccodes': "\"'",
        'a_ascii': "db",
        'a_byte': "db",
        'a_word': "dw",
        'a_dword': "dd",
        'a_qword': "dq",
        'a_oword': "xmmword",
        'a_float': "dd",
        'a_double': "dq",
        'a_tbyte': "dt",
        'a_dups': "#d dup(#v)",
        'a_bss': "%s dup ?",
        'a_seg': "seg",
        'a_curip': "$",
        'a_public': "public",
        'a_weak': "weak",
        'a_extrn': "extrn",
        'a_comdef': "",
        'a_align': "align",
        'lbrace': "(",
        'rbrace': ")",
        'a_mod': "%",
        'a_band': "&",
        'a_bor': "|",
        'a_xor': "^",
        'a_bnot': "~",
        'a_shl': "<<",
        'a_shr': ">>",
        'a_sizeof_fmt': "size %s",
    }
    
    # ----------------------------------------------------------------------
    def init_registers(self):
        """This function parses the register table and creates corresponding ireg_XXX constants"""

        # Registers definition
        self.reg_names = ["REG1", "REG2", "PTR", "PC", "CS", "DS"]

        # Create the ireg_XXXX constants
        for i in xrange(len(self.reg_names)):
            setattr(self, 'ireg_' + self.reg_names[i], i)

        # Segment register information (use virtual CS and DS registers):
        self.reg_first_sreg = self.ireg_CS
        self.reg_last_sreg  = self.ireg_DS

        # number of CS register
        self.reg_code_sreg = self.ireg_CS

        # number of DS register
        self.reg_data_sreg = self.ireg_DS
    
    # ----------------------------------------------------------------------
    def init_instructions(self):
        class idef:
            """
            Internal class that describes an instruction by:
            - instruction name
            - instruction decoding routine
            - canonical flags used by IDA
            """
            def __init__(self, name, cf, d, cmt = None):
                self.name = name
                self.cf  = cf
                self.d   = d
                self.cmt = cmt

        #
        # Instructions table (w/ pointer to decoder)
        #
        self.itable = {
            0x10: idef(name='XOR',      d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "REG1 = REG1 ^ REG2" ),
            0x11: idef(name='ADD',      d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "REG1 = REG1 + REG2" ),
            0x12: idef(name='LOAD',     d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "REG1 = *PTR" ),
            0x13: idef(name='STORE',    d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "*PTR = REG1" ),
            0x14: idef(name='SET_PTR',  d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "PTR = REG1" ),  
            0x15: idef(name='SWAP',     d=self.decode_NOP,      cf = 0x00,              cmt = lambda insn: "REG1 <-> REG2" ),
            0x20: idef(name='SET_REG1', d=self.decode_SETREG1,  cf = CF_USE1,           cmt = self.cmt_REG1),
            0x21: idef(name='JNZ',      d=self.decode_JNZ,      cf = CF_USE1 | CF_JUMP, cmt = self.cmt_JNZ),
        }

        # Now create an instruction table compatible with IDA processor module requirements
        Instructions = []
        i = 0
        for x in self.itable.values():
            d = dict(name=x.name, feature=x.cf)
            if x.cmt != None:
                d['cmt'] = x.cmt
            Instructions.append(d)
            setattr(self, 'itype_' + x.name, i)
            i += 1

        # icode of the last instruction + 1
        self.instruc_end = len(Instructions) + 1

        # Array of instructions
        self.instruc = Instructions

    # ----------------------------------------------------------------------
    def notify_ana(self, insn):
        """
        Decodes an instruction into insn
        """
        # take opcode byte
        opcode = insn.get_next_byte()

        # check supported opcode
        try:
            ins = self.itable[opcode]
            insn.itype = getattr(self, 'itype_' + ins.name)
        except:
            return 0

        # call the decoder
        return insn.size if ins.d(insn) else 0
    
    # ----------------------------------------------------------------------
    def notify_emu(self, insn):
        """
        Emulate instruction, create cross-references, plan to analyze
        subsequent instructions, modify flags etc. Upon entrance to this function
        all information about the instruction is in 'insn' structure.
        If zero is returned, the kernel will delete the instruction.
        """
        Feature = insn.get_canon_feature()

        if Feature & CF_USE1:
            self.handle_operand(insn, insn.Op1, 1)

        # Add flow
        if (Feature & CF_STOP == 0):
            add_cref(insn.ea, insn.ea + insn.size, fl_F)

        return 1
    
    # ----------------------------------------------------------------------
    def handle_operand(self, insn, op, isRead):

        optype = op.type

        if optype == o_near:
            add_cref(insn.ea, op.value, fl_JF)


    # ---------------------------------------------------------------------- 
    def notify_out_insn(self, ctx):
        """
        Generate text representation of an instruction in 'ctx.insn' structure.
        This function shouldn't change the database, flags or anything else.
        All these actions should be performed only by u_emu() function.
        """
        ctx.out_mnemonic()
        ctx.out_one_operand(0)
        ctx.set_gen_cmt()
        ctx.flush_outbuf()
    
    # ----------------------------------------------------------------------
    def notify_out_operand(self, ctx, op):
        """
        Generate text representation of an instructon operand.
        This function shouldn't change the database, flags or anything else.
        All these actions should be performed only by u_emu() function.
        The output text is placed in the output buffer initialized with init_output_buffer()
        This function uses out_...() functions from ua.hpp to generate the operand text
        Returns: 1-ok, 0-operand is hidden.
        """
        optype = op.type
              
        if optype == o_imm:
            ctx.out_value(op, OOFW_IMM | OOFS_NOSIGN | OOFW_8)
        
        elif optype == o_near:
           ctx.out_value(op, OOFW_IMM | OOFS_NOSIGN | OOFW_8)

        else:
            return False

        return True

    # ----------------------------------------------------------------------
    def notify_get_autocmt(self, insn):
        """
        Get instruction comment. 'insn' describes the instruction in question
        @return: None or the comment string
        """
        if 'cmt' in self.instruc[insn.itype]:
          return self.instruc[insn.itype]['cmt'](insn)


    # ----------------------------------------------------------------------
    # Instruction decoding
    # ----------------------------------------------------------------------

    # ----------------------------------------------------------------------
    def decode_SETREG1(self, insn):
        insn.Op1.type = o_imm
        insn.Op1.dtype = dt_byte
        insn.Op1.value = insn.get_next_byte()
        return True

    # ----------------------------------------------------------------------
    def decode_JNZ(self, insn):
        insn.Op1.type = o_near
        insn.Op1.dtype = dt_byte
        insn.Op1.value = insn.get_next_byte()
        return True
    
    # ----------------------------------------------------------------------
    def decode_NOP(self, insn):
        return True

    # ----------------------------------------------------------------------
    # Auto-commenting
    # ----------------------------------------------------------------------

    # ----------------------------------------------------------------------
    def cmt_REG1(self, insn):
        s = "REG1 = " + hex(int(insn.Op1.value))
        return s
    
    # ----------------------------------------------------------------------
    def cmt_JNZ(self, insn):
        s = "if REG1 != 0: goto " + hex(int(insn.Op1.value))
        return s

# ----------------------------------------------------------------------
def PROCESSOR_ENTRY():
    return kris_processor_t()
