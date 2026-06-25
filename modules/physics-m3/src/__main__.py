"""CLI entry point for physics-m3."""
import sys


def main():
    args = sys.argv[1:]
    if "--version" in args or "-V" in args:
        from physics_m3 import __version__

        print(f"physics-m3 v{__version__}")
    elif "--help" in args or "-h" in args or not args:
        print("Usage: physics-m3 [OPTIONS]")
        print("  --help, -h     Show this help")
        print("  --version, -V  Show version")
        print("  demo           Run the complete demo")
    elif args[0] == "demo":
        exec(open("demo_completa.py").read())
    else:
        print(f"Unknown command: {args[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
