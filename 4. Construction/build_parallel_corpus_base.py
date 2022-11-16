###
# Implementasi Pembentukan Parallel Corpus Dasar
###

import sqlite3
import os, sys, traceback
import unicodedata

INPUT_DB_PATH = 'db_kamus.db'
OUTPUT_DB_PATH = 'db_parallel_corpus_base.db'
OUTPUT_SCHEMA_PATH = 'schema_parallel_corpus.sql'
PREFIX_PUNCTUATIONS = "{[(“"
SUFFIX_PUNCTUATIONS = "}])”.,;:?!"

def generate_indexed_contoh(contoh_list):
  """ Teknis: Mengelompokkan contoh dari database menjadi urut per index """

  contoh_list_indexed = [None] * (len(contoh_list) // 2)
  for contoh in contoh_list:
    i = contoh['index'] - 1
    if i < 0 or i >= len(contoh_list_indexed):
      continue
    lang_i = {'MAD': 0, 'IND': 1}[contoh['bahasa']]
    if contoh_list_indexed[i] == None:
      contoh_list_indexed[i] = [None, None]
    contoh_list_indexed[i][lang_i] = contoh

  return contoh_list_indexed

def distribute_parallel(teks_list):
  """ Algoritma: Proses teks secara paralel """
  # Input: Ambil semua teks dalam satu contoh
  teks_mad_list, teks_ind_list = teks_list
  text_list_indexed = []
  # Teks Indonesia tidak kosong?
  if len(teks_ind_list) == 0:
    return []
  primary_teks_ind = None
  # Ambil satu pasang teks Indonesia paling awal (indeks 0)
  for teks_ind in teks_ind_list:
    if teks_ind['text'] != "":
      primary_teks_ind = teks_ind
      break
  # Teknis: Cek ganda teks Indonesia tidak kosong
  if primary_teks_ind == None:
    return []
  # Ambil semua pasang teks Madura
  for teks_mad in teks_mad_list:
    t = teks_mad['text']
    # Subproses: Deteksi Imbuhan (h)
    # Teks berakhir dengan (h)?
    if t.endswith('(h)'):
      # Pisah menjadi dua versi teks, satu tanpa "h", satu dengan "h".
      t = t[:-3]
      # Teknis: Tambahkan ke daftar pasang teks (versi dengan "h")
      text_list_indexed.append((t + 'h', primary_teks_ind['text']))
    if t:
      # Tambahkan ke daftar pasang teks
      text_list_indexed.append((t, primary_teks_ind['text']))
  return text_list_indexed

def distribute_sequential(teks_list):
  """ Algoritma: Proses teks secara berurutan """
  # Input: Ambil semua teks dalam satu contoh
  teks_mad_list, teks_ind_list = teks_list
  text_list_indexed = []
  # Ambil satu pasang teks (Madura dan Indonesia) urut dari indeks
  for i in range(min(len(teks_mad_list), len(teks_ind_list))):
    if (teks_mad_list[i]['text'] and teks_ind_list[i]['text']):
      # Tambahkan ke daftar pasang teks
      text_list_indexed.append((teks_mad_list[i]['text'], teks_ind_list[i]['text']))
  return text_list_indexed

def distribute_proverbs(teks_list):
  """ Algoritma: Proses teks secara peribahasa """
  # Input: Ambil semua teks dalam satu contoh
  teks_mad_list, teks_ind_list = teks_list
  teks_ind_list_join = ', '.join(map(lambda x: x['text'], teks_ind_list)).strip()
  # Teks Madura ada versi alternative?
  if len(teks_ind_list) == 0 or len(teks_mad_list) == 0 or \
    not teks_mad_list[-1]['alternative'] or not teks_ind_list_join:
    return []
  # Ambil satu pasang teks (Madura dan Indonesia), yang Madura ambil teks versi "alternative"
  # Tambahkan ke daftar pasang teks
  return [(teks_mad_list[-1]['alternative'], teks_ind_list_join)]

def normalize_text(text: str):
  # Normalisasi Unicode NFKD
  # Normalisasi Kapital (menjadi huruf kecil)
  return unicodedata.normalize('NFKD', text).lower()

def split_to_tokens(text: str):
  """ Algoritma: Pisah pasang teks menjadi pasang teks token """
  # Pisah masing-masing teks menjadi token dengan spasi
  text_list = text.strip().split(' ')
  text_list_split = []
  # Ambil satu token
  for word in text_list:
    postfixs = []
    # Ada tanda baca prefix atau suffix?
    while len(word) > 0:
      if word[0] in PREFIX_PUNCTUATIONS:
        # Pisahkan tanda baca (prefix)
        text_list_split.append(word[0])
        word = word[1:]
      elif word[-1] in SUFFIX_PUNCTUATIONS:
        # Pisahkan tanda baca (suffix)
        postfixs.append(word[-1])
        word = word[:-1]
      else:
        text_list_split.append(word)
        break
    text_list_split.extend(reversed(postfixs))
  return text_list_split

def index_tokens(teks, list_tokens, datamem_teks, datamem_token):
  """ Algoritma: Proses data pasang teks token """
  # Input: Inisialisasi daftar teks token ID
  teks_token = []
  # Ambil satu token
  for word in list_tokens:
    # token ada di tb_token?
    if word not in datamem_token:
      # Simpan token ke tb_token
      datamem_token[word] = len(datamem_token)
    # Ambil ID token, simpan ke daftar teks token ID
    token_id = datamem_token[word]
    teks_token.append((token_id, []))

  # Ambil permutasi pasangan dari daftar teks token ID
  for i, ta in enumerate(teks_token):
    neighbors_list = ta[1]
    for tb in teks_token[i+1:]:
      # Simpan data jarak teks token (neighbours)
      neighbors_list.append(tb[0])

  # Simpan daftar teks token ID ke tb_teks_token
  # Simpan ke tb_neighbour_teks_token
  datamem_teks.append((teks, teks_token))

def build_teks():
  """
  Algoritma: Program Utama Konstruksi Parallel Corpus
      dengan tokenisasi dasar dari database Kamus
  """
  # Input: Database dari Konstruksi Kamus
  con = sqlite3.connect(INPUT_DB_PATH)
  con.row_factory = sqlite3.Row
  cur = con.cursor()

  cur.execute('SELECT * FROM tb_kosakata')
  # Ambil satu kosakata
  for kosakata_index, kosakata in enumerate(cur.fetchall()):
    # Teknis: Muat data tb_contoh untuk kosakata ini
    cur.execute('SELECT * FROM tb_contoh WHERE kosakata_id = ?', (kosakata['id'],))
    contoh_list, kosakata_text = cur.fetchall(), kosakata['word']
    print(f'Processing {kosakata_index}: {kosakata_text}'.ljust(40, ' '), end='\r')
    try:
      contoh_list_indexed = generate_indexed_contoh(contoh_list)
      # Ambil satu pasangan contoh dalam kosakata
      for index, (contoh_mad, contoh_ind) in enumerate(contoh_list_indexed):
        # Pasangan pertama dalam kosakata?
        # Kosakata mempunyai keterangan linguistik?
        if kosakata['keterangan'] == "Ling" and index == 0:
          # Teknis: Lewati contoh ini
          continue
        text_list = [None, None]
        # Teknis: Muat data tb_teks untuk contoh ini
        cur.execute('SELECT * FROM tb_teks WHERE contoh_id = ?', (contoh_mad['id'],))
        text_list[0] = cur.fetchall()
        cur.execute('SELECT * FROM tb_teks WHERE contoh_id = ?', (contoh_ind['id'],))
        text_list[1] = cur.fetchall()
        text_list_indexed = []

        # Mempunyai keterangan pantun atau parmina?
        if contoh_mad['keterangan'] == 'Ptn' or contoh_mad['keterangan'] == 'Krm':
          # Subproses: Proses teks secara urut
          text_list_indexed = distribute_sequential(text_list)
        # Mempunyai keterangan peribahasa atau kiasan?
        elif contoh_mad['keterangan'] == 'Pb' or contoh_mad['keterangan'] == 'Ki':
          # Subproses: Proses teks secara peribahasa
          text_list_indexed = distribute_proverbs(text_list)
        else:
          # Subproses: Proses teks secara paralel
          text_list_indexed = distribute_parallel(text_list)

        # Teknis: Perulangan ini mewakili satu pasang teks dalam masing-masing subproses
        for index, (teks_mad, teks_ind) in enumerate(text_list_indexed):
          for lang, teks in [('MAD', teks_mad), ('IND', teks_ind)]:
            # Subproses: Normalisasi pasang teks
            nteks = normalize_text(teks)
            # Subproses: Pisah pasang teks menjadi pasang teks token
            tokens = split_to_tokens(nteks)
            # Simpan pasang teks ke tb_teks
            # Subproses: Proses data pasang teks token
            # Teknis: Yang disimpan pada tb_teks adalah teks setelah dinormalisasi
            index_tokens(nteks, tokens,
              datamem_teks_lang[lang],
              datamem_token_lang[lang])
    except:
      print(f'Error processing {kosakata_index}: {kosakata_text}')

def write_to_db():
  """ Proses: Simpan data tb_teks, tb_token, tb_teks_token, tb_neighbour_teks_token"""

  print('Writing to DB...'.ljust(40))

  # Teknis: Hapus Database lama jika ada
  if os.path.exists(OUTPUT_DB_PATH):
    os.remove(OUTPUT_DB_PATH)

  # Teknis: Buat Database baru
  con = sqlite3.connect(OUTPUT_DB_PATH)
  cur = con.cursor()
  with open(OUTPUT_SCHEMA_PATH, 'r', encoding='utf8') as f:
    cur.executescript(f.read())

  # Teknis: Struktur data {[index]: ID}
  datamem_tokenmaps = {'MAD': [], 'IND': []}
  SQL_TEKS_INSERT = 'INSERT INTO tb_teks (lang, text, "index") VALUES (?, ?, ?)'
  SQL_TOKEN_INSERT = 'INSERT INTO tb_token (lang, text, "index") VALUES (?, ?, ?)'
  SQL_TEKS_TOKEN_INSERT = 'INSERT INTO tb_teks_token (teks_id, token_id, "index") VALUES (?, ?, ?)'
  SQL_TEKS_TOKEN_NEIGHBOUR_INSERT = 'INSERT INTO tb_teks_token_neighbour (teks_id, token_id, ' + \
    'token_id_neighbour, distance) VALUES (?, ?, ?, ?)'

  try:
    # Teknis: Simpan data dari memori ke database
    for lang in ['MAD', 'IND']:
      datamem_token = datamem_token_lang[lang]
      datamem_tokenmap = datamem_tokenmaps[lang]
      datamem_tokenmap += [None] * (len(datamem_token))
      for token, index in datamem_token.items():
        # Teknis: Simpan pemetaan token dari index ke DB ID
        cur.execute(SQL_TOKEN_INSERT, (lang, token, index))
        datamem_tokenmap[index] = cur.lastrowid

    for lang in ['MAD', 'IND']:
      datamem_teks = datamem_teks_lang[lang]
      datamem_tokenmap = datamem_tokenmaps[lang]
      for index, (teks, teks_token) in enumerate(datamem_teks):
        cur.execute(SQL_TEKS_INSERT, (lang, teks, index))
        teks_id = cur.lastrowid
        for index, (token_index, neighbor_id_list) in enumerate(teks_token):
          token_id = datamem_tokenmap[token_index]
          cur.execute(SQL_TEKS_TOKEN_INSERT, (teks_id, token_id, index))
          for distance, neighbor_index in enumerate(neighbor_id_list):
            neighbor_id = datamem_tokenmap[neighbor_index]
            cur.execute(SQL_TEKS_TOKEN_NEIGHBOUR_INSERT,
              (teks_id, token_id, neighbor_id, distance))

    con.commit()
  except sqlite3.Error as er:
    print('SQLite error: %s' % (' '.join(er.args)))
    print("Exception class is: ", er.__class__)
    print('SQLite traceback: ')
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))

# Teknis: Variabel database dalam memori sementara
# Teknis: Struktur data:
# {[index]: (teks, teks_token [(id int,
#   {[distance]: neighbor_id int})]}
datamem_teks_lang = {'IND': [], 'MAD': []}
# Teknis: Struktur data: {[token]: index}
datamem_token_lang = {'IND': {}, 'MAD': {}}

try:
  build_teks()
except KeyboardInterrupt:
  pass
finally:
  write_to_db()
