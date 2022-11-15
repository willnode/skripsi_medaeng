# read

import h5py
import numpy as np
from torch.utils.data import DataLoader
from torch.nn import CrossEntropyLoss
from torch.optim import Adam
import torch
from tqdm import tqdm
from model import SkipGramEmbeddings
from torch.optim.lr_scheduler import LinearLR

BATCH_SIZE = 1000
LEARNING_RATE = 0.001
EPOCH = 2

def load_and_save(inp, dim, out):
    EMBEDDING_SIZE = dim
    with h5py.File(inp, 'r') as f:
        TOKEN_LENGTH = f['token'].shape[0]
        dataloader = DataLoader(torch.from_numpy(f['neighbor'][:]), batch_size=BATCH_SIZE, shuffle=True)
        model = SkipGramEmbeddings(TOKEN_LENGTH, EMBEDDING_SIZE)
        loss = CrossEntropyLoss()
        optim = Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-5)
        scheduler = LinearLR(optim, start_factor=1, end_factor=0, total_iters=EPOCH * len(dataloader))
        for epoch in range(EPOCH):
            loss_sum = 0
            num_examples = 0
            for data in tqdm(dataloader):
                optim.zero_grad()
                center, context, v = torch.transpose(data, 0, 1)
                v = v.view(-1, 1).repeat(1, dim)
                center_embed, context_embed = model(center, context, v)
                loss_rate = loss(center_embed, context_embed)
                loss_rate.backward()
                loss_sum += loss_rate.item()
                num_examples += len(data)
                optim.step()
                scheduler.step()
            print('Epoch: {} Loss: {}'.format(epoch, loss_sum / num_examples))
        torch.save({
            'embedding': model.word_embeds.weight.data.numpy(),
        }, out)

    
    



for lang in ['mad', 'ind']:
    for tknzr in ['base', 'wp8k']:
        for dim in [256, 512]:
            load_and_save(f'{tknzr}_{lang}.h5', dim, f'embedded_{dim}_{tknzr}_{lang}.h5')

