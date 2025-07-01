import threading
import time

class Emulator:

    def __init__(self):
        
        # State management
        self.running = False
        self.cycle_count = 0
        self.lock = threading.Lock()

        # Timers
        self.instruction_hz = 1/500
        self.clock_hz = 1/60

        # ROM
        self.rompath = None
        self.romdata = None

        # Memory
        self.memory = [0] * 4096

        # Registers

        self.program_counter = 0x200
        self.index_register = 0
        self.v = [0] * 16

        # Stack

        self.MAX_STACK_DEPTH = 16
        self.stack_pointer = 0
        self.stack = []

        # Timers

        self.delay_timer = 0
        self.sound_timer = 0

        # keypad

        self.keypad = [0] * 16
        
        # display

        self.display = [[0] * 64 for _ in range(32)]

        print("[INFO] CHIP-8 Emulator initialized")

    def loadrom(self,path):
        self.rompath = path
        print("[INFO] ROM path set")
    
    def readrom(self):
        try:
            with open(self.rompath, 'rb') as romfile:
                self.romdata = romfile.read()
                print("[INFO] ROM data read")
        except Exception as e:
            print(f"[ERROR] Failed to read ROM: {e}")
        
    def copytomem(self,start=0x200):
        if self.romdata:
            if len(self.romdata) < len(self.memory)-start:
                for address in range(len(self.romdata)):
                    self.memory[start+address] = self.romdata[address]
                print("[INFO] ROM copied to memory")
            else:
                print("[ERROR] ROM too large to be copied into memory")
        else:
             print("[ERROR] No Data in ROM to copy")

    def load_fontset(self):
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        
        for i in range(0,len(fontset)):
            self.memory[i + 0x50] = fontset[i]

        print("[INFO] Font set loaded into memory")
    
    def set_key(self,key,ispressed):
        try:
            if ((key >= 0) and (key <= 15)):
                self.keypad[key] = ispressed
            else:
                raise ValueError("Key out of bound")
        except Exception as e:
            print(f"[ERROR] keypad exception : {e}")

    def execute_opcode(self,opcode):
        x   = (opcode & 0x0F00) >> 8    # Fx15
        y   = (opcode & 0x00F0) >> 4    # 8xy6
        n   = opcode & 0x000F           # Dxyn
        nn  = opcode & 0x00FF           # Cxkk
        nnn = opcode & 0x0FFF           # Annn

        p1 = (opcode & 0xF000) >> 12  # first hex digit
        p2 = (opcode & 0x0F00) >> 8   # Second hex digit
        p3 = (opcode & 0x00F0) >> 4   # Third hex digit
        p4 = opcode & 0x000F          # Fourth hex digit

        if (opcode & 0xF000) == 0x0000: # 0nnn - SYS addr
            if opcode == 0x00E0:  # 00E0 - CLS
                self.display = [[0] * 64 for _ in range(32)]
                print("[EXEC] 0x00E0: Cleared screen")
            elif opcode == 0x00EE:  # 00EE - RET
                if self.stack:
                    self.program_counter = self.stack.pop()
                    self.stack_pointer -= 1
                    print("[EXEC] 0x00EE: Return from subroutine")
                else:
                    print("[ERROR] 0x00EE: Stack underflow")
            else:
                print(f"[EXEC] 0nnn: SYS Address {hex(nnn)} - Ignored")
        
        elif (opcode & 0xF000) == 0x1000: # 1nnn - JP addr
            self.program_counter = nnn
            print("[EXEC] 1nnn : Jumped Program counter to "+ hex(nnn))
        
        elif (opcode & 0xF000) == 0x2000: # 2nnn - CALL addr
            if len(self.stack) >= self.MAX_STACK_DEPTH :
                print("[ERROR] 2nnn : Stack overflow")
            else:
                self.stack.append(self.program_counter)
                self.stack_pointer += 1
                self.program_counter = nnn
                print("[EXEC] 2nnn : Call subroutine at "+hex(nnn))
        
        elif (opcode & 0xF000) == 0x3000: # 3xkk - SE Vx, byte
            if self.v[x] == nn:
                self.program_counter += 2
                print("[EXEC] 3xkk : Skip next instruction")
        
        elif (opcode & 0xF000) == 0x4000: # 4xkk - SNE Vx, byte
            if self.v[x] !=  nn:
                self.program_counter += 2
                print("[EXEC] 4xkk : Skip next instruction")
        
        elif (opcode & 0xF000) == 0x5000: # 5xy0 - SE Vx, Vy
            if self.v[x] == self.v[y]:
                self.program_counter += 2
                print("[EXEC] 5xy0 : Skip next instruction")

        elif (opcode & 0xF000) == 0x6000: # 6xkk - LD Vx, byte
            self.v[x] = nn
            print(f"[EXEC] 6xkk : Set v[{x}] to {hex(nn)}")
        
        elif (opcode & 0xF000) == 0x7000: # 7xkk - ADD Vx, byte
            self.v[x] = (self.v[x] + nn) & 0xFF
            print(f"[EXEC] 7xkk : Add {nn} to V[{x}], result: {self.v[x]}")

        elif (opcode & 0xF00F) == 0x8000: # 8xy0 - LD Vx, Vy
            self.v[x] = self.v[y]
            print(f"[EXEC] 8xy0 : Set v[{x}] to {self.v[x]}")

        elif (opcode & 0xF00F) == 0x8001: # 8xy1 - OR Vx, Vy
            self.v[x] |= self.v[y]
            print(f"[EXEC] 8xy1 : Set v[{x}] to {self.v[x]}")

        elif (opcode & 0xF00F) == 0x8002: # 8xy2 - AND Vx, Vy
            self.v[x] &= self.v[y]
            print(f"[EXEC] 8xy2 : Set v[{x}] to {self.v[x]}")
        
        elif (opcode & 0xF00F) == 0x8003: # 8xy3 - XOR Vx, Vy
            self.v[x] ^= self.v[y]
            print(f"[EXEC] 8xy3 : Set v[{x}] to {self.v[x]}")

        elif (opcode & 0xF00F) == 0x8004: # 8xy4 - ADD Vx, Vy
            result = self.v[x] + self.v[y]
            if result > 255:    
                self.v[0xF] = 1
                self.v[x] = result & 0xFF
                print(f"[EXEC] 8xy4 : Set v[{x}] to {self.v[x]} and v[F] to 1")
            
            else:
                self.v[0xF] = 0
                self.v[x] = result & 0xFF
                print(f"[EXEC] 8xy4 : Set v[{x}] to {self.v[x]} and v[F] to 0")

        elif (opcode & 0xF00F) == 0x8005: # 8xy5 - SUB Vx, Vy
            if self.v[x] > self.v[y]:
                self.v[0xF] = 1
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
                print(f"[EXEC] 8xy5: Set v[{x}] to {self.v[x]} and v[F] to {self.v[0xF]}")
            else:
                self.v[0xF] = 0
                self.v[x] = (self.v[x] - self.v[y]) & 0xFF
                print(f"[EXEC] 8xy5: Set v[{x}] to {self.v[x]} and v[F] to {self.v[0xF]}")
            
        
        elif (opcode & 0xF00F) == 0x8006: # 8xy6 - SHR Vx
            if (self.v[x] & 0x1) == 1:
                self.v[0xF] = 1
                self.v[x] = self.v[x] >> 1
                print(f"[EXEC] 8xy6 : Set v[{x}] to {self.v[x]} and v[F] to 1")
            else:
                self.v[0xF] = 0
                self.v[x] = self.v[x] >> 1
                print(f"[EXEC] 8xy6 : Set v[{x}] to {self.v[x]} and v[F] to 0")
        
        elif (opcode & 0xF00F) == 0x8007:  # 8xy7 - SUBN Vx, Vy
            if self.v[y] > self.v[x]:
                self.v[0xF] = 1
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
                print(f"[EXEC] 8xy7 : Set v[{x}] to {self.v[x]} and v[F] to 1")
            else:
                self.v[0xF] = 0
                self.v[x] = (self.v[y] - self.v[x]) & 0xFF
                print(f"[EXEC] 8xy7 : Set v[{x}] to {self.v[x]} and v[F] to 0")

        elif (opcode & 0xF00F) == 0x800E: # 8xyE - SHL Vx
            msb = self.v[x] >> 7
            if msb:
                self.v[0xF] = 1
                self.v[x] = (self.v[x] << 1) & 0xFF
                print(f"[EXEC] 8xyE : Set v[{x}] to {self.v[x]} and v[F] to 1")
            else:
                self.v[0xF] = 0
                self.v[x] = (self.v[x] << 1) & 0xFF
                print(f"[EXEC] 8xyE : Set v[{x}] to {self.v[x]} and v[F] to 0")

        elif (opcode & 0xF00F) == 0x9000: # 9xy0 - SNE Vx, Vy
            if self.v[x] != self.v[y]:
                self.program_counter += 2
                print("[EXEC] 9xy0 : Skip next instruction")

        elif (opcode & 0xF000) == 0xA000: # Annn - LD I, addr
            self.index_register = nnn
            print(f"[EXEC] Annn : Set index register to {self.index_register}")
        
        elif (opcode & 0xF000) == 0xB000: # Bnnn - JP V0, addr
            self.program_counter = self.v[0] + nnn
            print(f"[EXEC] Bnnn : Set program counter to {self.program_counter}")

        elif (opcode & 0xF000) == 0xC000: # Cxkk - RND Vx, byte
            import random
            rand_number = random.randint(0,255)
            self.v[x] = rand_number & nn
            print(f"[EXEC] Cxkk : Set v[x] to {self.v[x]}")

        elif (opcode & 0xF000) == 0xD000: # Dxyn - DRW Vx, Vy, nibble
            vx = self.v[x]
            vy = self.v[y]
            height = n
            self.v[0xF] = 0

            for row in range(height):
                sprite_data = self.memory[self.index_register + row]
                for col in range(8):
                    pixel = (sprite_data >> (7 - col)) & 1

                    x_coordinate = (vx + col) % 64
                    y_coordinate = (vy + row) % 32

                    if self.display[y_coordinate][x_coordinate] == 1 and pixel == 1:
                        self.v[0xF] = 1
                    
                    self.display[y_coordinate][x_coordinate] ^= pixel
            
            print(f"[EXEC] Dxyn : Drew Sprite on screen")

        elif (opcode & 0xF0FF) == 0xE09E: # Ex9E - SKP Vx
            vx = self.v[x]
            if self.keypad[vx] != 0:
                self.program_counter += 2
                print(f"[EXEC] Ex9E : Advanced the program counter [{x} is pressed]")

        elif (opcode & 0xF0FF) == 0xE0A1: # ExA1 - SKNP Vx
            vx = self.v[x]
            if self.keypad[vx] == 0:
                self.program_counter += 2
                print(f"[EXEC] ExA1 : Advanced the program counter [{x} is not pressed]")

        elif (opcode & 0xF0FF) == 0xF007: # Fx07 - LD Vx, DT
            with self.lock:
                self.v[x] = self.delay_timer
                print(f"[EXEC] Fx07 : Set vx to {self.v[x]}")
        
        elif (opcode & 0xF0FF) == 0xF00A: # Fx0A - LD Vx, K
            
            print(f"[EXEC] Fx0A : Waiting for Keypress")
            is_key_pressed = False

            for key in range(16):  
                if self.keypad[key] != 0:
                    self.v[x] = key
                    is_key_pressed = True
                    print(f"[EXEC] Fx0A : Key Pressed {hex(key)}")
                    break
            
            if not is_key_pressed:
                self.program_counter -= 2

        elif (opcode & 0xF0FF) == 0xF015: # Fx15 - LD DT, Vx
            with self.lock:
                self.delay_timer = self.v[x]
                print(f"[EXEC] Fx15 : Delay Timer updated to {self.delay_timer}")
        
        elif (opcode & 0xF0FF) == 0xF018: # Fx18 - LD ST, Vx
            with self.lock:
                self.sound_timer = self.v[x]
                print(f"[EXEC] Fx18 : Sound Timer updated to {self.sound_timer}")
        
        elif (opcode & 0xF0FF) == 0xF01E: # Fx1E - ADD I, Vx
            self.index_register = (self.index_register + self.v[x] ) & 0xFFFF
            print(f"[EXEC] Fx1E : Index Register updated to {hex(self.index_register)}")

        elif (opcode & 0xF0FF) == 0xF029: # LD F, Vx
            digit = self.v[x]
            self.index_register = 0x50 + (digit * 5)
            print(f"[EXEC] Fx1E : Index Register updated to {hex(self.index_register)}")
        
        elif (opcode & 0xF0FF) == 0xF033: # Fx33 - LD B, Vx
            value = self.v[x]
            self.memory[self.index_register] = value // 100
            self.memory[self.index_register + 1] = (value // 10) % 10
            self.memory[self.index_register + 2] = value % 10
            print(f"[EXEC] Fx33 : Updated memory from [{self.index_register} : {self.index_register + 2}] to {value}")

        elif (opcode & 0xF0FF) == 0xF055: # Fx55 - LD [I], Vx
            for i in range(0, x + 1):
                self.memory[self.index_register + i] = self.v[i]
            print(f"[EXEC] Fx55 : Updated memory from from {self.index_register} : {self.index_register + x + 1}")

        elif (opcode & 0xF0FF) == 0xF065: # Fx65 - LD Vx, [I]
            for i in range(0, x + 1):
                self.v[i] = self.memory[self.index_register + i]
            print(f"[EXEC] Fx65 : Updated register from from {self.index_register} : {self.index_register + x + 1}")

        else:
            print(f"[WARN] Unknown opcode: {hex(opcode)}")

    def cycle(self):
        high_byte = self.memory[self.program_counter]
        low_byte = self.memory[self.program_counter + 1]
        shifted_high = high_byte << 8

        opcode = shifted_high | low_byte
        self.program_counter += 2
        self.execute_opcode(opcode)

    def cpu_thread(self):
        print("[INFO] CPU Cycle Started")
        while self.running:
            start = time.time()
            self.cycle()
            end   = time.time()
            elapsed = end - start
            with self.lock:
                self.cycle_count += 1
            time.sleep(max(0, self.instruction_hz - elapsed))

        print(f"[INFO] {self.cycle_count} CPU cycles")

    def timer_thread(self):
        print("[INFO] Timer Cycle Started")
        while(self.running):
            with self.lock:
                if self.delay_timer > 0:
                    self.delay_timer -= 1
                if self.sound_timer > 0:
                    self.sound_timer -= 1
            time.sleep(self.clock_hz)
    
    def kill_emulator(self,max_cycle):
        while(self.running):
            with self.lock:
                if self.cycle_count > max_cycle:
                    self.running = False
                    print(f"[INFO] Emulator halted")
            time.sleep(self.instruction_hz)
    
    def start(self,cycles=None):
        cpu_thread_object = threading.Thread(target=self.cpu_thread, daemon=True)
        timer_thread_object = threading.Thread(target=self.timer_thread, daemon=True)
        if cycles:
            kill_thread_object = threading.Thread(target=self.kill_emulator, daemon=True, args=[cycles])

        self.running = True
        cpu_thread_object.start()
        timer_thread_object.start()
        if cycles:
            kill_thread_object.start()
            print("[INFO] Kill thread object")
        print(f"[INFO] CPU and Timer thread started")
                
    
# emu = Emulator()
# emu.loadrom(r"roms\IBM Logo.ch8")
# emu.readrom()
# emu.copytomem()
# emu.load_fontset()
# emu.start(25)

# while emu.running:
#     time.sleep(0.1)

# for row in emu.display:
#     print(''.join(['█' if pixel else ' ' for pixel in row]))