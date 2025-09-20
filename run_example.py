#!/usr/bin/env python3
"""
Simple script to run the unit example with different configurations.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from example import UnitExample


def run_configuration(name: str, use_mqtt: bool, use_rest: bool):
    """Run unit with specific configuration"""
    print(f"\n{'='*50}")
    print(f"Running: {name}")
    print(f"MQTT: {use_mqtt}, REST: {use_rest}")
    print(f"{'='*50}")
    
    try:
        unit = UnitExample(use_mqtt=use_mqtt, use_rest=use_rest)
        unit.start()
    except KeyboardInterrupt:
        print(f"\n{name} stopped by user")
    except Exception as e:
        print(f"Error in {name}: {e}")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        config = sys.argv[1].lower()
        
        if config == "1" or config == "none":
            run_configuration("Without MQTT and without REST", False, False)
        elif config == "2" or config == "mqtt":
            run_configuration("With MQTT but without REST", True, False)
        elif config == "3" or config == "rest":
            run_configuration("With REST but without MQTT", False, True)
        elif config == "4" or config == "both":
            run_configuration("With both MQTT and REST", True, True)
        else:
            print("Invalid configuration. Use: 1, 2, 3, 4, none, mqtt, rest, or both")
            return 1
    else:
        print("Pepeunit Unit Example Runner")
        print("============================")
        print("Usage: python run_example.py <configuration>")
        print()
        print("Configurations:")
        print("  1 or none  - Without MQTT and without REST")
        print("  2 or mqtt  - With MQTT but without REST")
        print("  3 or rest  - With REST but without MQTT")
        print("  4 or both  - With both MQTT and REST")
        print()
        print("Example: python run_example.py both")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
