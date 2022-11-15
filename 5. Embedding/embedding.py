# read

import sqlite3
from model import NEG_loss
import h5py
import numpy as np
from os.path import exists

from torch.utils.data import DataLoader
from torch.nn import CrossEntropyLoss
from torch.optim import Adam, SGD
import torch
from tqdm import tqdm
from torch.optim.lr_scheduler import LinearLR


CONTEXT_WINDOW = 3
NEGATIVE_SAMPLE = 6
BATCH_SIZE = 1000
LEARNING_RATE = 1
EPOCH = 1
DEVICE = 'cpu'

def print_config():
    print(CONTEXT_WINDOW, NEGATIVE_SAMPLE, BATCH_SIZE, LEARNING_RATE, EPOCH, DEVICE)

def load_from_db(db, lang):

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    token_list = ['[BOS]', '[EOS]', '[PAD]', '[UNK]']
    teks_list = {} # teks_list[teks_id] = [token_id]
    neighbor_list = [] # neighbor_list[teks_id][token_id][token_id] = <1 or -1>

    # Token list
    for row in cur.execute('SELECT * FROM tb_token where lang = ? ORDER BY "index"', [lang]):
        token_list.append(row['text'].encode("utf-8")) # ordered by index
    
    # Text list
    MAX = 0
    for row in cur.execute('''
SELECT tb_teks."index" as teks_index, tb_token."index" as token_index 
FROM tb_teks_token, tb_token, tb_teks 
WHERE tb_teks_token.token_id = tb_token.id AND tb_teks_token.teks_id = tb_teks.id 
AND tb_token.lang = ? ORDER BY tb_teks_token."index"''', [lang]):
        if row['teks_index'] not in teks_list:
            teks_list[row['teks_index']] = []
        teks_list[row['teks_index']].append(int(row['token_index']) + 4)
        MAX = max(MAX, int(row['teks_index']))

    # Positive neighborhood
    last_token = 0
    for row in cur.execute('''
SELECT t."index" index1, t2."index" index2 FROM tb_teks_token_neighbour ttn, tb_token t, tb_token t2 
WHERE ttn.token_id = t.id AND ttn.token_id_neighbour = t2.id 
AND t.lang = ? AND ttn.distance < ? ORDER BY ttn.id''', [lang, CONTEXT_WINDOW]):
        i1, i2 = int(row['index1']) + 4, int(row['index2']) + 4
        if i1 != last_token:
            neighbor_list.append({i1: []})
            last_token = i1
        neighbor_list[len(neighbor_list)-1][i1].append(i2)
    
    for tid in neighbor_list:
        for i in tid:
            if len(tid[i]) < CONTEXT_WINDOW:
                tid[i] += [2] * (CONTEXT_WINDOW - len(tid[i])) # Append with PAD
            if len(tid[i]) > CONTEXT_WINDOW:
                tid[i] = tid[i][:CONTEXT_WINDOW] # Truncate

    
    dutf8 = h5py.special_dtype(vlen=str)
    dvari = h5py.vlen_dtype(np.dtype('int32'))
    con.close()

    neighbor_input, neighbor_output = zip(*[[x, y] for n in neighbor_list for x, y in n.items()])
    return (
        np.array(token_list, dtype=dutf8), # token array
        np.array([[0, *teks_list.get(x, []), 1] for x in range(MAX + 1)], dtype=dvari), # teks array
        (np.array(neighbor_input), np.array(neighbor_output)), # neighbour array
    )


def data_gen(input, output): 
    dataloader_input = DataLoader(torch.from_numpy(input).to(DEVICE), batch_size=BATCH_SIZE, shuffle=False)
    dataloader_output = DataLoader(torch.from_numpy(output).to(DEVICE), batch_size=BATCH_SIZE, shuffle=False)
    iter_input = iter(dataloader_input)
    iter_output = iter(dataloader_output)
    for i in range(len(dataloader_input)):
        yield next(iter_input), next(iter_output)

def train_embedding(token, neigbour, dim, data, log):
    EMBEDDING_SIZE = dim
    TOKEN_LENGTH = token.shape[0]
    dataloader = list(data_gen(*neigbour))
    model = NEG_loss(TOKEN_LENGTH, EMBEDDING_SIZE, device=DEVICE).train().to(DEVICE)
    
    optim = Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = LinearLR(optim, start_factor=1, end_factor=0, total_iters=EPOCH * len(dataloader))
    epoch = 0
    if data is not None: 
        model.load_state_dict(data['state'])
        optim.load_state_dict(data['optimizer'])
        scheduler.load_state_dict(data['scheduler'])
        epoch = data['epoch']
    try:
        with open(log, 'a') as f:
            while epoch < EPOCH:
                loss_sum = 0
                num_examples = 0
                for data in dataloader:
                    optim.zero_grad(set_to_none=True)
                    center, context = data
                    loss = model(center, context, NEGATIVE_SAMPLE)
                    loss.backward()
                    loss_sum += loss.item()
                    num_examples += len(data)
                    optim.step()
                    scheduler.step()
                loggg = 'Epoch: {} Loss: {}'.format(epoch, loss_sum / num_examples)
                print(loggg)
                f.write(loggg + '\n')
                epoch += 1
    except KeyboardInterrupt:
        pass
    return {
        'state': model.state_dict(),
        'optimizer': optim.state_dict(),
        'scheduler': scheduler.state_dict(),
        'epoch': epoch,
    }

def load_and_train(db, output):
    mad = load_from_db(db, 'MAD')
    ind = load_from_db(db, 'IND')
    max_v_teks = min(len(mad[1]), len(ind[1]))
    max_h_teks = max(max(len(x) for x in mad[1]), max(len(x) for x in ind[1]))

    data = {
        'MAD': {
            'token': mad[0],
            'embedding': {
                256: None,
                512: None,
            },
        },
        'IND': {
            'token': ind[0],
            'embedding': {
                256: None,
                512: None,
            },
        },
        'TEKS': np.swapaxes(np.array([
                [np.pad(x, (0, max_h_teks - len(x)), constant_values=2) for x in mad[1][:max_v_teks]], 
                [np.pad(x, (0, max_h_teks - len(x)), constant_values=2) for x in ind[1][:max_v_teks]], 
            ], dtype=np.int32), 0, 1),
    }
    
    if exists(output):
        data = torch.load(output, map_location=torch.device(DEVICE))

    for dim in [256, 512]:
        data['MAD']['embedding'][dim] = train_embedding(mad[0], mad[2], dim, data['MAD']['embedding'][dim], output + '.log')
        data['IND']['embedding'][dim] = train_embedding(ind[0], ind[2], dim, data['IND']['embedding'][dim], output + '.log')

    torch.save(data, output)
