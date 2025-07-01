import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def parse_arguments():
    parser = argparse.ArgumentParser(description="CHIP-8 Emulator")
    
    parser.add_argument(
        '--rom', '-r',
        type=str,
        help='Path to the CHIP-8 ROM file to load'
    )
    
    parser.add_argument(
        '--cycles', '-c',
        type=int,
        default=None,
        help='Number of CPU instructions to execute (default: infinite)'
    )
    
    return parser.parse_args()


def run_development_gui(rom_path, max_cycles):
    try:
        from PyQt6.QtWidgets import QApplication
        from runtime.dev_mode import DevModeGUI
        
        print("Launching CHIP-8 Development GUI...")
        
        app = QApplication(sys.argv)
        window = DevModeGUI()
        
        # Load ROM if specified
        if rom_path:
            print(f"Loading ROM: {rom_path}")
            try:
                window.emu.loadrom(rom_path)
                window.emu.readrom()
                window.emu.copytomem()
                window.emu.load_fontset()
                window.rom_path_label.setText(f"Loaded: {os.path.basename(rom_path)}")
                window.start_btn.setEnabled(True)
                print("ROM loaded successfully!")
            except Exception as e:
                print(f"Error loading ROM: {e}")
                window.rom_path_label.setText(f"Error: {str(e)}")
        
        # Set max cycles if specified
        if max_cycles:
            window.max_cycles = max_cycles
            print(f"Emulator will stop after {max_cycles} instructions")
        else:
            window.max_cycles = None
        
        window.show()
        return app.exec()
        
    except ImportError as e:
        print("ImportError"+ str(e)+"\n\nTry running 'uv sync'")
        return 1


def main():
    print("CHIP-8 Emulator v1.0")
    print("=" * 30)
    
    args = parse_arguments()
    
    print(f"ROM: {args.rom or 'None'}")
    print(f"Max cycles: {args.cycles or 'Infinite'}")
    print()
    
    return run_development_gui(args.rom, args.cycles)


if __name__ == "__main__":
    sys.exit(main())