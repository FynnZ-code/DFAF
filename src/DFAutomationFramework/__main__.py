import argparse
import importlib

def main():
    parser = argparse.ArgumentParser(
        description="Test Description"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--Master", action="store_true", help="Startet Master")
    group.add_argument("--Worker", action="store_true", help="Startet einen Worker")
    
    parser.add_argument(
        "--Tasks",
        type=str,
        default="Dummy",
        help="Listet die ausführbaren Prozesse Kommagetrent (nur für Worker relevant)"
    )
    parser.add_argument(
        "--TPLogging",
        action="store_true",
        help="Aktiviert Thirdparty Logging. Sollte nur für debugging Zwecke genutzt werden."
    )

    args = parser.parse_args()
    if args.Master:
        master_module = importlib.import_module("DFAutomationFramework.Master")
        master_module.main(args.TPLogging)
    elif args.Worker:
        worker_module = importlib.import_module("DFAutomationFramework.Worker")
        worker_module.main(tasks=args.Tasks)

if __name__ =="__main__":
    main()