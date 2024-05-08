import os

filename = "C:\\Users\\frank\\NTUSER.DAT"

print(f"{os.stat(filename).st_size} bytes")
print(f"{os.stat(filename).st_size / (1024 * 1024)} Mbytes")