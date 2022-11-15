import glob, os

files = []
for file in glob.glob("*0.txt"):
    with open(file, "r", encoding='utf8') as f:
        files.append(f.read().strip())

with open('c_output.txt', "w", encoding='utf8') as f:
    f.write('\n'.join(files))
