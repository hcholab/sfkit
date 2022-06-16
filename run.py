from src.protocol.validate_data import validate_data
from src.protocol.run_protocol import run_protocol
import sys

if len(sys.argv) < 2:
    print("Usage: python run.py <validate_data | run_protocol>")
    exit(1)
if sys.argv[1] == "validate_data":
    if len(sys.argv) > 2 and sys.argv[2] == "--user":
        validate_data("Alpha", sys.argv[3])
    else:
        validate_data("Alpha", "a@a.com")
elif sys.argv[1] == "run_protocol":
    run_protocol("Alpha", "a@a.com")
else:
    print("Usage: python run.py <validate_data | run_protocol>")
    exit(1)
exit(0)
