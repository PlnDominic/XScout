import argparse
from xscout.scheduler import XScoutScheduler

def main():
    parser = argparse.ArgumentParser(description="XScout: Autonomous Lead Discovery Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending actual notifications")
    args = parser.parse_args()

    agent = XScoutScheduler(dry_run=args.dry_run)
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\n[!] Stopping XScout Agent...")

if __name__ == "__main__":
    main()
