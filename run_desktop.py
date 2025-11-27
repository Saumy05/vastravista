#!/usr/bin/env python3
"""
VastraVista Desktop Launcher
Helps users choose between Streamlit and OpenCV versions
"""

import sys
import subprocess
import os

def print_banner():
    print("\n" + "="*60)
    print("👗 VASTRAVISTA DESKTOP - AR FASHION TRY-ON")
    print("="*60)
    print()

def main():
    print_banner()
    
    print("Choose your preferred interface:")
    print()
    print("1. Streamlit Desktop App (Recommended)")
    print("   - Modern UI with chat interface")
    print("   - Real-time recommendations panel")
    print("   - Best for interactive use")
    print()
    print("2. OpenCV Standalone")
    print("   - Lightweight, full-screen interface")
    print("   - Lower resource usage")
    print("   - Best for performance")
    print()
    print("3. Exit")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting Streamlit Desktop App...")
        print("   Press Ctrl+C to stop\n")
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", "vastravista_desktop.py"])
        except KeyboardInterrupt:
            print("\n\n✅ Application stopped")
        except FileNotFoundError:
            print("\n❌ Error: Streamlit not found. Install with: pip install streamlit")
            sys.exit(1)
    
    elif choice == "2":
        print("\n🚀 Starting OpenCV Standalone App...")
        print("   Press Q or ESC to quit\n")
        try:
            subprocess.run([sys.executable, "vastravista_opencv.py"])
        except KeyboardInterrupt:
            print("\n\n✅ Application stopped")
        except FileNotFoundError:
            print("\n❌ Error: Could not start application")
            sys.exit(1)
    
    elif choice == "3":
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("\n❌ Invalid choice. Please run again and select 1, 2, or 3.")
        sys.exit(1)

if __name__ == "__main__":
    main()

