#####
# Implementasi Konstruksi Database Kamus
#####

import sqlite3
import os, sys, traceback

INPUT_TEXT_PATH = '../3. Correction/c_output.txt'
OUTPUT_DB_PATH = 'db_kamus.db'
OUTPUT_SCHEMA_PATH = 'schema_database_kamus.sql'

def proses_teks(contoh, contoh_id, kosakata_id, index):
    """ Algoritma: Proses Teks """

    # Teknis: Inisialisasi variabel untuk data teks
    text, context, alternative, pos, ref, i = '', None, None, None, None, 0

    try:
        # Ambil satu karakter dalam teks
        while i < len(contoh):
            # Karakter adalah kurung kotak "["?
            if contoh[i] == '[':
                # Ambil teks sampai "]"
                while contoh[i] != ']':
                    i += 1
                # Simpan sebagai prononsiasi di tb_kosakata
                # Teknis: Sudah tersimpan di proses terpisah

            # Karakter adalah kurung kurawal "{"?
            elif contoh[i] == '{':
                refBegin = i
                # ambil teks sampai "}"
                while contoh[i] != '}':
                    i += 1
                refEnd = i
                ref = contoh[refBegin+1:refEnd]
                # Teks merupakan keterangan untuk contoh?
                if ref in ['Pb', 'Ki', 'Krm', 'Ptn']:
                    # Simpan sebagai keterangan di tb_contoh
                    add_ref_contoh(ref, contoh_id)
                    ref = None
                # Teknis: Jika ref != None maka nanti ref...
                # Simpan sebagai keterangan di tb_teks
            
            # Karakter adalah kurung lengkung "("?
            elif contoh[i] == '(':
                # Teknis: Deteksi tanda ttg.
                isTtg = contoh[i+1:i+6] == 'ttg. '
                if isTtg:
                    i += 5
                # ambil teks sampai ")"
                # Teknis: Perlu mendukung kurung rekursif
                altBegin = i
                recursive = 1
                while recursive > 0:
                    i += 1
                    if contoh[i] == '(':
                        recursive += 1
                    elif contoh[i] == ')':
                        recursive -= 1
                altEnd = i
                # Teks merupakan keterangan konteks?
                if isTtg:
                    # simpan sebagai "konteks" untuk tb_teks
                    context = contoh[altBegin+1:altEnd]
                else:
                    # simpan sebagai keterangan di tb_teks
                    alternative = contoh[altBegin+1:altEnd]
            else:
                # Ambil teks sampai satu kata
                wordBegin = i
                while i < len(contoh) and contoh[i] != ' ':
                    i += 1
                # Teknis: Jika ket. promomina, lanjutkan pengambilan sampai lengkap
                for prons in ['persona tunggal', 'persona pertama jamak', 'persona pertama tunggal']:
                    if contoh[wordBegin:i + f' {prons}.'.__len__()] == f'Pron {prons}.':
                        i += f' ${prons}.'.__len__()
                wordEnd = i
                word = contoh[wordBegin:wordEnd]
                # Kata merupakan keterangan teks?
                if word in ['a.', 'Adv.', 'n.', 'Num.', 'P.', 'Pron.', 'Pron persona tunggal.', 'Pron persona pertama jamak.', 'Pron persona pertama tunggal.', 'v.', 'Ling.']:
                    pos = word[:-1]
                    # Kata merupakan keterangan linguistik?
                    if pos == 'Ling':
                        # Simpan sebagai keterangan untuk tb_kosakata
                        add_ref_kosakata(pos, kosakata_id)
                        pos = None
                    # Teknis: Jika bukan keterangan linguistik, maka nanti pos...
                    # simpan sebagai keterangan "kelas kata" untuk tb_teks

                # Teknis: Abaikan angka (kemungkinan indeks homonim)
                elif word.isnumeric():
                    pass
                else:
                    # Simpan data "teks" (tambah dari kata yang sudah ada) untuk tb_teks
                    text += word.rstrip('.') + ' '
            i += 1
        
        # Simpan data tb_teks
        cur.execute(
            'INSERT INTO tb_teks (contoh_id, text, context, alternative, keterangan, kelas_kata, "index") VALUES (?, ?, ?, ?, ?, ?, ?)',
            (contoh_id, text.strip(), context, alternative, ref, pos, index))
    except Exception as e:
        print("Processing error at text:", contoh)
        print(e)

def split_teks_list_by_comma(contoh):
    """ Teknis: Pisah dengan tanda koma "," sebagai daftar "teks" """
    """ Teknis: Proses ini memperhatikan tanda kurung sehingga tidak salah memisahkan """

    group_level = 0
    texts = []
    text = ''
    for c in contoh:
        if c == ',':
            if group_level == 0 and text != '':
                texts.append(text)
                text = ''
                continue
        elif c == '(' or c == '[' or c == '{':
            group_level += 1
        elif c == ')' or c == ']' or c == '}':
            group_level -= 1
        if text != '' or c != ' ':
            text += c
    if group_level != 0:
        print("Error: group level not 0: ", contoh)
    if text != '':
        texts.append(text)
    return texts

def split_contoh_list_by_dot_comma(kosakata_contoh):
    """ Teknis: Pisah dengan tanda titik koma ";" sebagai daftar "contoh" """
    """ Teknis: Proses ini memperhatikan tanda kurung sehingga tidak salah memisahkan """

    group_level = 0
    contohs = []
    contoh = ''
    for c in kosakata_contoh:
        if c == ';':
            if group_level == 0 and contoh != '':
                contohs.append(contoh.strip())
                contoh = ''
                continue
        elif c == '(' or c == '[' or c == '{':
            group_level += 1
        elif c == ')' or c == ']' or c == '}':
            group_level -= 1
        if contoh != '' or c != ' ':
            contoh += c
    if group_level != 0:
        print("Error: group level not 0: ", kosakata_contoh)
    if contoh != '':
        contohs.append(contoh)
    return contohs

def split_lang_list_by_equal_sign(kosakata_contoh):
    """ Teknis: Pisah dengan tanda sama dengan "=" untuk memisahkan 2 bahasa """
    """ Teknis: Proses ini memperhatikan tanda kurung sehingga tidak salah memisahkan """

    group_level = 0
    contohs = []
    contoh = ''
    for c in kosakata_contoh:
        if c == '=':
            if group_level == 0 and contoh != '':
                contohs.append(contoh.strip())
                contoh = ''
                continue
        elif c == '(' or c == '[' or c == '{':
            group_level += 1
        elif c == ')' or c == ']' or c == '}':
            group_level -= 1
        if contoh != '' or c != ' ':
            contoh += c
    if group_level != 0:
        print("Error: group level not 0: ", kosakata_contoh)
    if contoh != '':
        contohs.append(contoh)
    return contohs

def find_prononciation_part(contoh):
    """ Teknis: Ambil teks prononsiasi dari contoh pertama """

    parts = contoh.split(' ')
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            return part
    return None

def find_homonym_index_part(contoh: str):
    """ Teknis: Ambil index homonim dari contoh pertama """

    parts = contoh.split(' ')
    for part in parts:
        if part.isnumeric():
            return part
    return 1

def find_primary_contoh(contoh):
    """ Teknis: Ambil contoh pertama """

    first_contoh = contoh.split(';')[0]
    first_contoh_mad = first_contoh.split('=')[0]
    first_contoh = first_contoh_mad.split(',')[0]
    return first_contoh

def add_ref_contoh(ref, contoh_id):
    """ Teknis: Simpan sebagai keterangan di tb_contoh """

    cur.execute(
        'UPDATE tb_contoh SET keterangan = ? WHERE id = ?',
        (ref,
        contoh_id),
    )

def add_ref_kosakata(ref, kosakata_id):
    """ Teknis: Simpan sebagai keterangan untuk tb_kosakata """

    cur.execute(
        'UPDATE tb_kosakata SET keterangan = ? WHERE id = ?',
        (ref,
        kosakata_id),
    )

def main():
    """ Algoritma: Program Utama Konstruksi Data Kamus dari Scan """

    # Input: Teks hasil scan dan perbaikan dari Kamus
    input_text = open(INPUT_TEXT_PATH, 'r', encoding='utf8')

    try:
        # Ambil satu paragraf sebagai satu "kosakata"
        for kosakata_text in input_text.readlines():
            primary_contoh = find_primary_contoh(kosakata_text)

            # Simpan data tb_kosakata
            # Teknis: Menyimpan ke DB perlu didahulukan sehingga mendapat ID terakhir
            cur.execute(
                'INSERT INTO tb_kosakata (word, pronounciation, homonym_index) VALUES (?, ?, ?)',
                (kosakata_text.split(' ')[0],
                find_prononciation_part(primary_contoh),
                find_homonym_index_part(primary_contoh)))
            kosakata_id = cur.lastrowid

            # Pisah dengan tanda titik koma ";" sebagai daftar "contoh"
            for contoh_idx, contoh in enumerate(split_contoh_list_by_dot_comma(kosakata_text)):
                # Pisah dengan tanda sama dengan "=" untuk memisahkan 2 bahasa
                contoh_parts = split_lang_list_by_equal_sign(contoh)

                # Teknis: Tampilkan error jika jumlahnya bahasanya salah
                if len(contoh_parts) != 2:
                    print('Error: invalid contoh:', contoh)
                    continue

                [rawtext_mad, rawtext_ind] = contoh_parts
                rawtext_mad = rawtext_mad.strip()
                rawtext_ind = rawtext_ind.strip()

                # Simpan data tb_contoh (2 bahasa terpisah)
                # Teknis: Menyimpan ke DB perlu didahulukan, ini bagian untuk bahasa Madura 
                cur.execute(
                    'INSERT INTO tb_contoh (rawtext, bahasa, "index", kosakata_id) VALUES (?, ?, ?, ?)',
                    (rawtext_mad, "MAD", contoh_idx + 1, kosakata_id))

                contoh_id = cur.lastrowid

                # Pisah dengan tanda koma "," sebagai daftar "teks"
                for index, contoh in enumerate(split_teks_list_by_comma(rawtext_mad)):
                    # Subproses: Proses Teks (bahasa Madura)
                    proses_teks(contoh.strip(), contoh_id, kosakata_id, index + 1)

                # Simpan data tb_contoh (2 bahasa terpisah)
                # Teknis: Menyimpan ke DB perlu didahulukan, ini bagian untuk bahasa Indonesia 
                cur.execute(
                    'INSERT INTO tb_contoh (rawtext, bahasa, "index", kosakata_id) VALUES (?, ?, ?, ?)',
                    (rawtext_ind, "IND", contoh_idx + 1, kosakata_id))

                contoh_id = cur.lastrowid

                # Pisah dengan tanda koma "," sebagai daftar "teks"
                for index, contoh in enumerate(split_teks_list_by_comma(rawtext_ind)):
                    # Subproses: Proses Teks (bahasa Indonesia)
                    proses_teks(contoh.strip(), contoh_id, kosakata_id, index + 1)

        # Simpan tb_kosakata, tb_contoh dan tb_teks ke Database
        input_text.close()
        con.commit()
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

# Teknis: Hapus Database lama jika ada
if os.path.exists(OUTPUT_DB_PATH):
    os.remove(OUTPUT_DB_PATH)

# Teknis: Buat Database baru
con = sqlite3.connect(OUTPUT_DB_PATH)
cur = con.cursor()
with open(OUTPUT_SCHEMA_PATH, 'r', encoding='utf8') as f:
    cur.executescript(f.read())

main()
