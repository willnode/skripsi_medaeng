
import sqlite3
import os, sys, traceback


INPUT_DB_PATH = 'db_parallel_corpus_base.db'
OUTPUT_DB_PATH = 'db_parallel_corpus_wp8k.db'
OUTPUT_SCHEMA_PATH = 'schema_parallel_corpus.sql'
TARGET_VOCAB_SIZE = 8000

def merge_token(a: str, b: str):
  """ Teknis: Gabungkan dua token menjadi satu token """
  return a + b[1:]

def split_singles_token(word: str):
  """ Algoritma: Pisahkan token menjadi per karakter token """
  return [word[0]] + ['_' + x for x in word[1:]]

def build_token_list(lang, vocab_set):
  # Inisialisasi daftar kosakata terpisah dengan jumlah penggunaannya
  list_token_data = []
  list_token_count = []
  # Hitung jumlah penggunaan tb_token dari tb_teks_token (database dasar)
  cur.execute('SELECT "id", "text", "index", "count" FROM token_count WHERE lang = ?', (lang,))
  # Ambil satu tb_token dan jumlah penggunaannya
  for _, vocab in enumerate(cur.fetchall()):
    # Subproses: Pisah token menjadi per karakter token
    token_list = split_singles_token(vocab['text'])
    # Simpan ke daftar kosakata terpisah
    list_token_data.append(token_list)
    list_token_count.append(vocab['count'])
    # Ambil satu per karakter token
    for token in token_list:
      # Masukkan atau tambahkan jumlah ke dalam daftar kosakata baru
      if token not in vocab_set:
        vocab_set[token] = vocab['count']
      else:
        vocab_set[token] += vocab['count']

  # ... Sampai memenuhi target jumlah token
  while len(vocab_set) < TARGET_VOCAB_SIZE:
    # Subproses: Temukan pasangan token terbaik selanjutnya
    # Inisialisasi daftar token berpasangan
    pair_set = {}
    all_done = False
    # Muat data daftar kosakata terpisah
    for i in range(len(list_token_data)):
      # Ambil satu dari daftar kosakata terpisah
      token_data = list_token_data[i]
      token_count = list_token_count[i]
      # Ambil pasangan token dari satu kosakata terpisah
      for j in range(len(token_data) - 1):
        all_done = True
        # Tambahkan pasangan token ke daftar token berpasangan beserta jumlah penggunaannya
        pair = (token_data[j], token_data[j+1])
        if pair not in pair_set:
          pair_set[pair] = token_count
        else:
          pair_set[pair] += token_count
    # Teknis: Apabila tidak ada pasangan token yang ditemukan, berhenti
    if not all_done:
      break
    # Inisialisasi daftar skor token berpasangan
    pair_scores = {}
    # Ambil satu dari daftar token berpasangan
    for pair, count in pair_set.items():
      # Hitung skor wordpiece
      pair_scores[pair] = count / (vocab_set[pair[0]] + vocab_set[pair[1]])
    # Cari pasangan dengan skor tertinggi
    best_pair = max(pair_scores.items(), key=lambda x: x[1])[0]
    # Pasangan dengan skor tertinggi ditemukan...
    # Masukkan ke dalam daftar kosakata baru
    vocab_set[merge_token(*best_pair)] = pair_set[best_pair]

    # Subproses: Sesuaikan daftar kosakata terpisah untuk menggunakan gabungan kosakata baru
    for i in range(len(list_token_data)):
      # Ambil satu dari daftar kosakata terpisah
      token_data: list = list_token_data[i]
      # Ambil satu token dan satu token berikutnya
      j = 0
      while j < len(token_data) - 1:
        # Token baru sama seperti token ini digabung?
        if token_data[j] == best_pair[0] and token_data[j+1] == best_pair[1]:
          # Gabung dan simpan daftar baru ke daftar kosakata terpisah
          token_data.pop(j)
          token_data.pop(j)
          token_data.insert(j, merge_token(*best_pair))
        j += 1
    print(f'Vocab size: {len(vocab_set)}, best pair: {best_pair}'.ljust(80), end='\r')

def split_token_to_wp(token: str, vocab_set: dict):
  start, end, wp = 0, len(token), []
  while start < len(token):
    subset = token[start:end]
    if start > 0:
      subset = '_' + subset
    if subset in vocab_set:
      wp.append(subset)
      start = end
      end = len(token)
    else:
      end -= 1
      if end < 1:
        print('Error: token not found in vocab_set ', subset)
        break
  return wp

def build_teks(lang, vocab_set, datamem_teks, datamem_token):
    """ Algoritma: Baca tb_teks (database dasar) dan terapkan menggunakan kosakata Wordpiece """

    # Input: Muat data tb_teks, tb_token, tb_teks_token dari database dasar
    cur.execute('SELECT * FROM tb_teks where lang = ? order by "id"', (lang,))
    list_teks = cur.fetchall()
    cur.execute('SELECT * FROM tb_token where lang = ?', (lang,))
    list_token = cur.fetchall()
    list_token_converted = {}
    cur.execute('SELECT * FROM tb_teks_token order by "index"')
    list_teks_token = cur.fetchall()
    # Input: Inisialisasi daftar mapping dari token dasar ke token wordpiece
    map_teks_token = {}
    # Ambil satu token dari tb_token
    for token in list_token:
      # Subproses: Pisah token sesuai dengan daftar kosakata wordpiece
      splitted_token = split_token_to_wp(token['token'], vocab_set)
      # Simpan ke daftar mapping token dasar ke token wordpiece
      list_token_converted[token['id']] = splitted_token
    for teks_token in list_teks_token:
      if teks_token['teks_id'] not in map_teks_token:
        map_teks_token[teks_token['teks_id']] = []
      map_teks_token[teks_token['teks_id']].append(teks_token['token_id'])
    for i, vocab in enumerate(vocab_set):
      datamem_token[vocab] = i
    # Ambil satu teks dari tb_teks
    for teks in list_teks:
      # Inisialisasi daftar token baru untuk teks
      teks_token = []
      # Ambil satu token dari tb_teks_token dalam teks terkait
      for token in map_teks_token[teks['id']]:
        # Dari token tersebut, cari daftar token baru dari mapping token dasar ke token wordpiece
        teks_token.extend(list_token_converted[token])
      # Simpan ke daftar token baru untuk teks
      teks_token = list(map(lambda x: (datamem_token[x], []), teks_token))
      # Subproses: Proses teks token
      for i, ta in enumerate(teks_token):
        neighbors_list = ta[1]
        for tb in teks_token[i+1:]:
          neighbors_list.append(tb[0])
      datamem_teks.append((teks['text'], teks_token))

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
# Teknis: Struktur data: {[token]: count}
wp_token_lang = {'IND': {}, 'MAD': {}}


# Input: Data dari Parallel Corpus dasar
con = sqlite3.connect(INPUT_DB_PATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

# Per bahasa di dalam parallel corpus
for lang in ['MAD', 'IND']:
  try:
    # Inisialisasi daftar kosakata wordpiece dengan jumlah penggunaannya
    build_token_list(lang, wp_token_lang[lang])
    # Simpan daftar kosakata wordpiece ke tb_token
  except KeyboardInterrupt:
    pass
  finally:
    # Baca tb_teks (database dasar) dan terapkan menggunakan kosakata Wordpiece
    build_teks(lang, wp_token_lang[lang],
      datamem_teks_lang[lang],
      datamem_token_lang[lang])

con.close()
write_to_db()

