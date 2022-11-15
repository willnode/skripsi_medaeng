# read

import sqlite3
import h5py
import numpy as np

CONTEXT_WINDOW = 3
NEGATIVE_SAMPLE = 6

def load_and_save(db, lang, filename):

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    token_list = ['[BOS]', '[EOS]', '[UNK]', '[PAD]']
    teks_list = {} # teks_list[teks_id] = [token_id]
    neighbor_list = {} # neighbor_list[token_id][token_id] = <1 or -1>

    # Token list
    for row in cur.execute('SELECT * FROM token where lang = ? ORDER BY "index"', [lang]):
        neighbor_list[len(token_list)] = {}
        token_list.append(row['text'].encode("utf-8")) # ordered by index
    
    # Text list
    for row in cur.execute('SELECT teks_token.teks_id, token."index" FROM teks_token, token where teks_token.token_id = token.id AND token.lang = ?', [lang]):
        if row['teks_id'] not in teks_list:
            teks_list[row['teks_id']] = []
        teks_list[row['teks_id']].append(int(row['index']) + 4)

    # Positive neighborhood
    for row in cur.execute('SELECT t."index" index1, t2."index" index2 FROM teks_token_neighbour ttn, token t , token t2 WHERE ttn.token_id = t.id AND ttn.token_id_neighbour = t2.id AND t.lang = ? AND ttn.distance < ?', [lang, 2]):
        i1, i2 = int(row['index1']) + 4, int(row['index2']) + 4
        neighbor_list[i1][i2] = 1
        neighbor_list[i2][i1] = 1

    # Negative neighborhood
    for key in neighbor_list:
        for _ in range(NEGATIVE_SAMPLE):
            i2 = np.random.randint(4, len(token_list))
            while (i2 in neighbor_list[key] or i2 == key) and len(neighbor_list[key]) < len(token_list) - 5:
                i2 = np.random.randint(4, len(token_list))
            neighbor_list[key][i2] = -1

        
    with h5py.File(filename, 'w') as f:
        dutf8 = h5py.string_dtype(encoding='utf-8')
        f.create_dataset('token', data=np.array(token_list, dtype=dutf8))
        dvari = h5py.vlen_dtype(np.dtype('int32'))
        varlist = [np.array(x) for x in teks_list.values()]
        f.create_dataset('teks', data=np.array(varlist, dtype=dvari))
        f.create_dataset('neighbor', data=np.array([(x, y, v) for x in neighbor_list for y, v in neighbor_list[x].items()]))


    con.close()

load_and_save('../4. Construction/dataset_db.db', 'IND', 'base_ind.h5')
load_and_save('../4. Construction/dataset_db.db', 'MAD', 'base_mad.h5')
load_and_save('../4. Construction/dataset_wordpiece_db.db', 'IND', 'wp8k_ind.h5')
load_and_save('../4. Construction/dataset_wordpiece_db.db', 'MAD', 'wp8k_mad.h5')
