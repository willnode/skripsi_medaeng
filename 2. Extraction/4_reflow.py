# Convert all to single line,
# Then split by glossary

import re
import unicodedata

# Open input & output
input_text = open('kamus_4_pdf2text.txt', 'r', encoding='utf8')
output_text = open('kamus_5_split.txt', 'w', encoding='utf8')

# read and normalize unicode
texts = '\n'.join(input_text.readlines())
texts = unicodedata.normalize('NFKD', texts)

# init variables
glossaryMatrix = [[]]
refGroup = 0
refWord = 0
indoMode = False

# scan each characters
for pos, ch in enumerate(texts):
    # don't scan dot char inside brackets
    if ch in ['(', '[', '{']:
        refGroup += 1
    if ch in [')', ']', '}']:
        refGroup -= 1

    # new page character, skip
    if ch == "\x0c":
        continue

    # assume new line == a space
    if ch == "\n":
        ch = ' '

    # (madura = indonesia), switch mode
    # also it's impossible to have = inside brackets
    # so also normalize our refGroup back to 0
    if ch == "=":
        indoMode = True
        refGroup = 0
    # (indonesia ; madura), switch mode
    if ch == ";":
        indoMode = False

    # append character to current glosary
    glossaryMatrix[len(glossaryMatrix) - 1].append(ch)

    # a valid dot char means end of glosary
    # valid means: not in brackets and in indo mode
    if ch == '.' and refGroup == 0 and indoMode:
        # sometimes there's faulty if ; is not scanned properly
        # so it's stuck in indo mode. another way to make sure
        # the dot is valid is make sure the next dot is an alphabets
        pos2 = pos + 1
        while pos2 < len(texts) and texts[pos2].isspace():
            pos2 += 1
        if pos2 < len(texts) and not texts[pos2].isalpha():
            continue

        # set new glosary
        glossaryMatrix.append([])
        indoMode = False

for x in glossaryMatrix:
    output = ''.join(x)
    # delete book header (odd)
    output = re.sub(r" *\d{0,2}(1|3|5|7|9) +Kamus Madura *", " ", output)
    # delete book header (even)
    output = re.sub(r" *Kamus Madura +\d{0,2}(2|4|6|8|0) *", " ", output)
    # trim multi space
    output = re.sub(r" +", " ", output).strip()
    output_text.write(output)
    output_text.write("\n")

input_text.close()
output_text.close()


