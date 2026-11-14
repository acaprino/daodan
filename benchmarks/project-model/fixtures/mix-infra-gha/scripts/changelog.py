import subprocess

log = subprocess.run(["git", "log", "--oneline", "-20"], capture_output=True, text=True, check=True)
print(log.stdout)
