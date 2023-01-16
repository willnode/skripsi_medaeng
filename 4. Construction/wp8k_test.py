
def merge_token(a: str, b: str):
    """ Teknis: Gabungkan dua token menjadi satu token """
    return a + b[1:]


def split_singles_token(word: str):
    """ Algoritma: Pisahkan token menjadi per karakter token """
    return [word[0]] + ['_' + x for x in word[1:]]


def build(words):
    # Inisialisasi daftar kosakata terpisah dengan jumlah penggunaannya
    list_token_data = []
    list_token_count = []
    vocab_set = {}
    # Ambil satu tb_token dan jumlah penggunaannya
    for vocab, le in words.items():
      # Subproses: Pisah token menjadi per karakter token
        token_list = split_singles_token(vocab)
        # Simpan ke daftar kosakata terpisah
        list_token_data.append(token_list)
        list_token_count.append(le)
        # Ambil satu per karakter token
        for token in token_list:
            # Masukkan atau tambahkan jumlah ke dalam daftar kosakata baru
            if token not in vocab_set:
                vocab_set[token] = le
            else:
                vocab_set[token] += le
    # ... Sampai memenuhi target jumlah token
    while len(vocab_set) < 14:
        print(len(vocab_set))
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
            pair_scores[pair] = count / \
                (vocab_set[pair[0]] + vocab_set[pair[1]])
        # Cari pasangan dengan skor tertinggi
        best_pair = max(pair_scores.items(), key=lambda x: x[1])[0]
        print(best_pair)
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
    
    return vocab_set


print(build({
    "orèng": 2,
    "loros": 3,
    "polong": 4,
}))
