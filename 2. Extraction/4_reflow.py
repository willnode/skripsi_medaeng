###
# Program untuk memisahkan data baris berdasarkan kosakata
###

import re
import unicodedata

# Buka file input dan output
input_text = open('3_pdf2text_output.txt', 'r', encoding='utf8')
output_text = open('5_reflow_output.txt', 'w', encoding='utf8')

# Baca file input dan normalisasikan unicode NFKD
texts = '\n'.join(input_text.readlines())
texts = unicodedata.normalize('NFKD', texts)

# Inisialisasi Variabel
glossaryMatrix = [[]]
refGroup = 0
refWord = 0
indoMode = False

# Pindah setiap karakter
for pos, ch in enumerate(texts):
    # Jangan pindai jika didalam kurung
    if ch in ['(', '[', '{']:
        refGroup += 1
    if ch in [')', ']', '}']:
        refGroup -= 1

    # Jangan pindai penanda halaman baru
    if ch == "\x0c":
        continue

    # Asumsikan baris baru adalah spasi
    if ch == "\n":
        ch = ' '

    # Tanda sama dengan berarti selanjutnya bhs Indonesia
    # Jarang ada tanda sama dengan didalam kurung,
    # Jadi apabila ada tanda ini, set refGroup ke 0
    if ch == "=":
        indoMode = True
        refGroup = 0
    # Tanda titik koma brarti selanjutnya bhs Madura
    if ch == ";":
        indoMode = False

    # Tambah karakter ke kosakata terakhir
    glossaryMatrix[len(glossaryMatrix) - 1].append(ch)

    # Tanda titik yang valid berarti kosakata selesai
    # valid berarti: tidak didalam kurung dan dalam bhs Indonesia
    if ch == '.' and refGroup == 0 and indoMode:
        # Sering ada titik koma disalah artikan sebagai hal yang lain,
        # Pastikan sehabis titik koma lanjutannya adalah alfabet.
        pos2 = pos + 1
        while pos2 < len(texts) and texts[pos2].isspace():
            pos2 += 1
        if pos2 < len(texts) and not texts[pos2].isalpha():
            continue

        # Tambah kosakata baru
        glossaryMatrix.append([])
        indoMode = False

for x in glossaryMatrix:
    output = ''.join(x)
    # Hapus header buku (ganjil)
    output = re.sub(r" *\d{0,2}(1|3|5|7|9) +Kamus Madura *", " ", output)
    # Hapus header buku (genap)
    output = re.sub(r" *Kamus Madura +\d{0,2}(2|4|6|8|0) *", " ", output)
    # Hapus spasi ganda
    output = re.sub(r" +", " ", output).strip()
    output_text.write(output)
    output_text.write("\n")

# Selesai. Tutup file
input_text.close()
output_text.close()


