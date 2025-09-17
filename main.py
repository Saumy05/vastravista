#!/usr/bin/env python3
"""
VastraVista - AI-Powered Fashion Recommendation System
Main Entry Point

Author: Saumya Tiwari
B.Tech CSE 7th Semester - AKS University
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.integration.main_controller import VastraVistaController
from src.utils.file_handler import setup_logging

def main():
    """Main function to start VastraVista application"""
    
    # Setup logging
    setup_logging()
    
    print("�� VastraVista - AI Fashion Recommendation System")
    print("=" * 50)
    print("Modules Available:")
    print("1. Cloth Detection")
    print("2. Color Extraction")
    print("3. Skin Tone Analysis")
    print("4. Recommendation Engine")
    print("5. Virtual Try-On")
    print("6. Complete Pipeline")
    print("=" * 50)
    
    try:
        # Initialize main controller
        controller = VastraVistaController()
        
        # Start the application
        controller.start_application()
        
    except KeyboardInterrupt:
        print("\n👋 Thank you for using VastraVista!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
