import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from emulator.emulator import Emulator

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QDialog, QTableWidget,
    QTableWidgetItem, QFileDialog, QFrame, QGroupBox,
    QScrollArea, QSizePolicy, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont, QPainter, QColor, QKeyEvent, QPalette, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal

class MemoryViewer(QDialog):
    def __init__(self, memory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Memory Viewer")
        self.resize(600, 700)
        self.memory = memory
        
        # Modern styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                color: #ecf0f1;
            }
            QTableWidget {
                background-color: #34495e;
                alternate-background-color: #2c3e50;
                color: #ecf0f1;
                gridline-color: #7f8c8d;
                border: 2px solid #3498db;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.table = QTableWidget(4096, 2)
        self.table.setHorizontalHeaderLabels(["Address", "Value (Hex)"])
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.update_table()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(500)

    def update_table(self):
        for i in range(4096):
            addr_item = QTableWidgetItem(f"0x{i:03X}")
            val_item = QTableWidgetItem(f"0x{self.memory[i]:02X}")
            addr_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            val_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(i, 0, addr_item)
            self.table.setItem(i, 1, val_item)

class StackViewer(QDialog):
    def __init__(self, stack, stack_pointer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stack Viewer")
        self.resize(400, 500)
        self.stack = stack
        self.stack_pointer = stack_pointer
        
        # Modern styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                color: #ecf0f1;
            }
            QListWidget {
                background-color: #34495e;
                color: #ecf0f1;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                font-family: 'Consolas';
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #7f8c8d;
            }
            QListWidget::item:selected {
                background-color: #e74c3c;
            }
        """)

        self.list_widget = QListWidget()
        
        sp_label = QLabel(f"Stack Pointer: {self.stack_pointer}")
        sp_label.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        sp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(sp_label)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.update_stack()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stack)
        self.timer.start(500)

    def update_stack(self):
        self.list_widget.clear()
        for i, addr in enumerate(self.stack):
            item = QListWidgetItem(f"[{i}] 0x{addr:03X}")
            if i == len(self.stack) - 1:  # Highlight current stack top
                item.setBackground(QColor("#e74c3c"))
            self.list_widget.addItem(item)

class ModernButton(QPushButton):
    def __init__(self, text, color="#3498db", parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setFixedHeight(40)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(color)}, stop:1 {color});
            }}
            QPushButton:pressed {{
                background: {self.darken_color(color)};
            }}
            QPushButton:disabled {{
                background: #7f8c8d;
                color: #bdc3c7;
            }}
        """)

    def darken_color(self, color):
        color_map = {
            "#3498db": "#2980b9",
            "#2ecc71": "#27ae60",
            "#e74c3c": "#c0392b",
            "#f39c12": "#d68910",
            "#9b59b6": "#8e44ad"
        }
        return color_map.get(color, "#2c3e50")
    
    def lighten_color(self, color):
        color_map = {
            "#3498db": "#5dade2",
            "#2ecc71": "#58d68d",
            "#e74c3c": "#ec7063",
            "#f39c12": "#f8c471",
            "#9b59b6": "#bb8fce"
        }
        return color_map.get(color, "#34495e")

class KeypadButton(QPushButton):
    keyPressed = pyqtSignal(int)
    keyReleased = pyqtSignal(int)
    
    def __init__(self, key_value, key_label, parent=None):
        super().__init__(key_label, parent)
        self.key_value = key_value
        self.setFixedSize(50, 50)
        self.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.is_pressed = False
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:1 #2c3e50);
                color: #ecf0f1;
                border: 2px solid #7f8c8d;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #34495e);
                border-color: #3498db;
            }
            QPushButton:pressed {
                background: #3498db;
                border-color: #2980b9;
            }
        """)

    def set_pressed(self, pressed):
        self.is_pressed = pressed
        if pressed:
            self.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    border: 2px solid #2980b9;
                    border-radius: 8px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #34495e, stop:1 #2c3e50);
                    color: #ecf0f1;
                    border: 2px solid #7f8c8d;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #7f8c8d, stop:1 #34495e);
                    border-color: #3498db;
                }
            """)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.keyPressed.emit(self.key_value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.keyReleased.emit(self.key_value)

class RegisterLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 4px 8px;
                margin: 1px;
            }
        """)
        self.animation = QPropertyAnimation(self, b"styleSheet")
        self.animation.setDuration(1000)
        
    def highlight_change(self):
        # Green highlight animation for changed values
        self.animation.setStartValue("""
            QLabel {
                background-color: #2ecc71;
                color: white;
                border: 1px solid #27ae60;
                border-radius: 4px;
                padding: 4px 8px;
                margin: 1px;
            }
        """)
        self.animation.setEndValue("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 4px 8px;
                margin: 1px;
            }
        """)
        self.animation.start()

class DisplayWidget(QWidget):
    def __init__(self, emulator, scale=12, parent=None):
        super().__init__(parent)
        self.emulator = emulator
        self.scale = scale
        self.setFixedSize(64 * scale + 4, 32 * scale + 4)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw border
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#2c3e50"))
        
        for y in range(32):
            for x in range(64):
                pixel = self.emulator.display[y][x]
                color = QColor("#00ff41") if pixel else QColor("#001100")  # Matrix green theme
                painter.fillRect(
                    x * self.scale + 2,
                    y * self.scale + 2,
                    self.scale,
                    self.scale,
                    color
                )

class DevModeGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CHIP-8 Emulator - Development Mode")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern dark theme
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                color: #ecf0f1;
                font-family: 'Segoe UI';
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #7f8c8d;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #3498db;
            }
        """)

        self.emu = Emulator()
        self.previous_registers = [0] * 16  # Track previous register values for highlighting
        
        # Keyboard mapping for CHIP-8
        self.key_map = {
            Qt.Key.Key_1: 0x1, Qt.Key.Key_2: 0x2, Qt.Key.Key_3: 0x3, Qt.Key.Key_4: 0xC,
            Qt.Key.Key_Q: 0x4, Qt.Key.Key_W: 0x5, Qt.Key.Key_E: 0x6, Qt.Key.Key_R: 0xD,
            Qt.Key.Key_A: 0x7, Qt.Key.Key_S: 0x8, Qt.Key.Key_D: 0x9, Qt.Key.Key_F: 0xE,
            Qt.Key.Key_Z: 0xA, Qt.Key.Key_X: 0x0, Qt.Key.Key_C: 0xB, Qt.Key.Key_V: 0xF
        }
        
        # Reverse mapping for visual keypad
        self.reverse_key_map = {v: k for k, v in self.key_map.items()}
        
        self.keypad_buttons = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Left Column - Display and Controls
        left_column = QVBoxLayout()
        
        # Header
        header = QLabel("CHIP-8 Emulator")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #3498db; margin-bottom: 20px;")
        
        # Control Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.load_rom_btn = ModernButton("Load ROM", "#3498db")
        self.start_btn = ModernButton("Start", "#2ecc71")
        self.stop_btn = ModernButton("Stop", "#e74c3c")
        self.reset_btn = ModernButton("Reset", "#f39c12")
        
        self.load_rom_btn.clicked.connect(self.load_rom)
        self.start_btn.clicked.connect(self.start_emulator)
        self.stop_btn.clicked.connect(self.stop_emulator)
        self.reset_btn.clicked.connect(self.reset_emulator)
        
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.load_rom_btn)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.reset_btn)

        # Display
        display_group = QGroupBox("Display (64x32)")
        display_layout = QVBoxLayout()
        self.display_widget = DisplayWidget(self.emu, scale=12)
        display_layout.addWidget(self.display_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        display_group.setLayout(display_layout)

        # Keypad
        keypad_group = QGroupBox("Keypad")
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(5)
        
        # CHIP-8 keypad layout
        keypad_layout_map = [
            ['1', '2', '3', 'C'],
            ['4', '5', '6', 'D'],
            ['7', '8', '9', 'E'],
            ['A', '0', 'B', 'F']
        ]
        
        keypad_values = [
            [0x1, 0x2, 0x3, 0xC],
            [0x4, 0x5, 0x6, 0xD],
            [0x7, 0x8, 0x9, 0xE],
            [0xA, 0x0, 0xB, 0xF]
        ]
        
        for row in range(4):
            for col in range(4):
                key_value = keypad_values[row][col]
                key_label = keypad_layout_map[row][col]
                button = KeypadButton(key_value, key_label)
                button.keyPressed.connect(self.on_keypad_press)
                button.keyReleased.connect(self.on_keypad_release)
                keypad_layout.addWidget(button, row, col)
                self.keypad_buttons[key_value] = button
        
        keypad_group.setLayout(keypad_layout)

        left_column.addWidget(header)
        left_column.addLayout(button_layout)
        left_column.addWidget(display_group)
        left_column.addWidget(keypad_group)
        left_column.addStretch()

        # Right Column - System State
        right_column = QVBoxLayout()
        
        # Registers
        registers_group = QGroupBox("Registers")
        self.registers_layout = QGridLayout()
        self.registers_layout.setSpacing(5)
        self.register_labels = []
        
        for i in range(16):
            label = RegisterLabel(f"V{i:X}: 00")
            self.registers_layout.addWidget(label, i // 4, i % 4)
            self.register_labels.append(label)
        
        registers_group.setLayout(self.registers_layout)

        # System Info
        system_group = QGroupBox("System State")
        system_layout = QVBoxLayout()
        
        self.pc_label = RegisterLabel("PC: 0x200")
        self.index_label = RegisterLabel("I: 0x000")
        self.cycles_label = RegisterLabel("Cycles: 0")
        self.delay_timer_label = RegisterLabel("Delay Timer: 0")
        self.sound_timer_label = RegisterLabel("Sound Timer: 0")
        self.stack_pointer_label = RegisterLabel("Stack Pointer: 0")
        
        system_layout.addWidget(self.pc_label)
        system_layout.addWidget(self.index_label)
        system_layout.addWidget(self.cycles_label)
        system_layout.addWidget(self.delay_timer_label)
        system_layout.addWidget(self.sound_timer_label)
        system_layout.addWidget(self.stack_pointer_label)
        
        system_group.setLayout(system_layout)

        # Debug Tools
        debug_group = QGroupBox("Debug Tools")
        debug_layout = QVBoxLayout()
        
        self.memory_btn = ModernButton("Memory Viewer", "#9b59b6")
        self.stack_btn = ModernButton("Stack Viewer", "#e67e22")
        
        self.memory_btn.clicked.connect(self.open_memory_viewer)
        self.stack_btn.clicked.connect(self.open_stack_viewer)
        
        debug_layout.addWidget(self.memory_btn)
        debug_layout.addWidget(self.stack_btn)
        
        debug_group.setLayout(debug_layout)

        # ROM Info
        rom_group = QGroupBox("ROM Information")
        rom_layout = QVBoxLayout()
        
        self.rom_path_label = QLabel("No ROM loaded")
        self.rom_path_label.setWordWrap(True)
        self.rom_path_label.setStyleSheet("color: #bdc3c7; font-style: italic;")
        
        rom_layout.addWidget(self.rom_path_label)
        rom_group.setLayout(rom_layout)

        right_column.addWidget(registers_group)
        right_column.addWidget(system_group)
        right_column.addWidget(debug_group)
        right_column.addWidget(rom_group)
        right_column.addStretch()

        # Combine columns
        main_layout.addLayout(left_column, 2)
        main_layout.addLayout(right_column, 1)
        
        self.setLayout(main_layout)

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_state)
        self.update_timer.start(50)  # 20 FPS update rate

    def load_rom(self):
        file_dialog = QFileDialog()
        rom_path, _ = file_dialog.getOpenFileName(
            self, 
            "Open CHIP-8 ROM File", 
            "roms/", 
            "CHIP-8 ROMs (*.ch8 *.rom);;All Files (*)"
        )
        if rom_path:
            try:
                self.emu.loadrom(rom_path)
                self.emu.readrom()
                self.emu.copytomem()
                self.emu.load_fontset()
                self.rom_path_label.setText(f"Loaded: {os.path.basename(rom_path)}")
                self.rom_path_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
                self.start_btn.setEnabled(True)
            except Exception as e:
                self.rom_path_label.setText(f"Error loading ROM: {str(e)}")
                self.rom_path_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def start_emulator(self):
        if not self.emu.running:
            # Use max_cycles if set, otherwise run indefinitely
            max_cycles = getattr(self, 'max_cycles', None)
            if max_cycles:
                self.emu.start(max_cycles)
                print(f"[INFO] Emulator started with max cycles: {max_cycles}")
            else:
                self.emu.start()
                print("[INFO] Emulator started (infinite cycles)")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

    def stop_emulator(self):
        if self.emu.running:
            self.emu.running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def reset_emulator(self):
        self.stop_emulator()
        self.emu = Emulator()
        self.rom_path_label.setText("No ROM loaded")
        self.rom_path_label.setStyleSheet("color: #bdc3c7; font-style: italic;")
        self.start_btn.setEnabled(False)

    def open_memory_viewer(self):
        self.memory_viewer = MemoryViewer(self.emu.memory, self)
        self.memory_viewer.show()

    def open_stack_viewer(self):
        self.stack_viewer = StackViewer(self.emu.stack, self.emu.stack_pointer, self)
        self.stack_viewer.show()

    def on_keypad_press(self, key_value):
        self.emu.set_key(key_value, 1)
        self.keypad_buttons[key_value].set_pressed(True)

    def on_keypad_release(self, key_value):
        self.emu.set_key(key_value, 0)
        self.keypad_buttons[key_value].set_pressed(False)

    def update_state(self):
        # Update registers with change highlighting
        for i in range(16):
            current_value = self.emu.v[i]
            if current_value != self.previous_registers[i]:
                self.register_labels[i].highlight_change()
                self.previous_registers[i] = current_value
            self.register_labels[i].setText(f"V{i:X}: 0x{current_value:02X}")
        
        # Update system state
        self.pc_label.setText(f"PC: 0x{self.emu.program_counter:03X}")
        self.index_label.setText(f"I: 0x{self.emu.index_register:03X}")
        
        with self.emu.lock:
            self.cycles_label.setText(f"Cycles: {self.emu.cycle_count}")
            self.delay_timer_label.setText(f"Delay Timer: {self.emu.delay_timer}")
            self.sound_timer_label.setText(f"Sound Timer: {self.emu.sound_timer}")
        
        self.stack_pointer_label.setText(f"Stack Pointer: {self.emu.stack_pointer}")
        
        # Update display
        self.display_widget.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in self.key_map:
            key_value = self.key_map[event.key()]
            self.emu.set_key(key_value, 1)
            if key_value in self.keypad_buttons:
                self.keypad_buttons[key_value].set_pressed(True)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() in self.key_map:
            key_value = self.key_map[event.key()]
            self.emu.set_key(key_value, 0)
            if key_value in self.keypad_buttons:
                self.keypad_buttons[key_value].set_pressed(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DevModeGUI()
    window.show()
    sys.exit(app.exec())
