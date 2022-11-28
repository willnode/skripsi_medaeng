
import torch
import torch.nn as nn
import copy, math
import unicodedata

BOS_TOKEN = 0
EOS_TOKEN = 1
PAD_TOKEN = 2
UNK_TOKEN = 3

def clones(module, N):
  "Produce N identical layers."
  return nn.ModuleList([copy.deepcopy(module) for _ in range(N)])

def attention(query, key, value, mask=None, dropout=None):
  "Compute 'Scaled Dot Product Attention'"
  d_k = query.size(-1)
  scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)
  if mask is not None:
    scores = scores.masked_fill(mask == 0, -1e9)
  p_attn = scores.softmax(dim=-1)
  if dropout is not None:
    p_attn = dropout(p_attn)
  return torch.matmul(p_attn, value), p_attn

def subsequent_mask(size):
  "Mask out subsequent positions."
  attn_shape = (1, size, size)
  subsequent_mask = torch.triu(torch.ones(attn_shape), diagonal=1).type(
    torch.uint8
  )
  return subsequent_mask == 0

def rate_warmup(step, model_size, warmup):
  """
  we have to default the step to 1 for LambdaLR function
  to avoid zero raising to negative power.
  """
  if step == 0:
    step = 1
  return (
    model_size ** (-0.5) * min(step ** (-0.5), step * warmup ** (-1.5))
  )

def rate_decay(step, decay, init):
  return init/(1+decay*step)


def _nest_wp_tokenize(word: bytes, vocab: map, need_prefix=False):
  i = len(word)
  while i > 0:
    candidate = ('_' if need_prefix else '').encode('UTF-8') + word[:i]
    if candidate in vocab:
      return [candidate] + _nest_wp_tokenize(word[i:], vocab, True)
    i -= 1
  return [] if need_prefix else ['[UNK]']

def tokenize(text: list, vocab: map, wordpiece=False, debug=False):
  result = []
  for t in text:
    src_tokenized = unicodedata.normalize('NFKD',t).lower().strip().split(' ')
    src_tokenized = [x.encode('UTF-8') for x in src_tokenized]
    if wordpiece:
      words = []
      for i in range(len(src_tokenized)):
        words.extend(_nest_wp_tokenize(src_tokenized[i], vocab))
      src_tokenized = words
    debug and print('src_tokenized', [x.decode('UTF-8') for x in src_tokenized])
    src_indexed = [vocab.get(x, UNK_TOKEN) for x in src_tokenized]
    result.append([BOS_TOKEN, *src_indexed, EOS_TOKEN])
    debug and print('src_indexed', result[-1])

  if len(result) > 1:
    max_len = max([len(x) for x in result])
    for i in range(len(result)):
      result[i] += [PAD_TOKEN] * (max_len - len(result[i]))
  return torch.tensor(result)

def detokenize(text: torch.Tensor, vocab: list, debug=False):
  result = []
  for t in text.cpu():
    debug and print('dst_indexed', t)
    dst_tokenized = [vocab[x] for x in t if x > 3]
    dst_tokenized = [x.decode('utf8') for x in dst_tokenized]
    debug and print('dst_tokenized', dst_tokenized)
    teks = []
    for token in dst_tokenized:
      if token.startswith('_'):
        teks.append(token[1:])
      else:
        teks.append(' ')
        teks.append(token)
    result.append(''.join(teks).strip())
  return result






