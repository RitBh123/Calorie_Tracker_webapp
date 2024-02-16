import importlib.util
import subprocess
import sys

# Function to install missing libraries
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check if pandas is installed, if not, install it
spec = importlib.util.find_spec("pandas")
if spec is None:
    print("Installing pandas...")
    install("pandas")

# Check if pymongo is installed, if not, install it
spec = importlib.util.find_spec("pymongo")
if spec is None:
    print("Installing pymongo...")
    install("pymongo")

# Check if flask is installed, if not, install it
spec = importlib.util.find_spec("flask")
if spec is None:
    print("Installing flask...")
    install("flask")

# Check if datetime is installed, if not, install it
spec = importlib.util.find_spec("datetime")
if spec is None:
    print("Installing datetime...")
    install("datetime")