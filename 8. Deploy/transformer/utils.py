
import torch
import torch.nn as nn
import copy, math
import unicodedata

BOS_TOKEN = 0
EOS_TOKEN = 1
PAD_TOKEN = 2
UNK_TOKEN = 3
PREFIX_PUNCTUATIONS = tuple("{[(“")
SUFFIX_PUNCTUATIONS = tuple("}])”.,;:?!")

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
      cand =  _nest_wp_tokenize(word[i:], vocab, True)
      if len(cand) == 0 and not need_prefix and i != len(word):
        break # assume UNK word for non subword
      return [candidate] + cand
    i -= 1
  return [] if need_prefix else ['[UNK]']

def split_tokens(text: str):
    src_tokenized = unicodedata.normalize('NFKD',text).lower().strip().split(' ')
    # split by punctuations
    i = 0
    while i < len(src_tokenized):
      tmp = src_tokenized[i]
      while tmp.startswith(PREFIX_PUNCTUATIONS):
        src_tokenized[i] = tmp[1:]
        src_tokenized.insert(i, tmp[0])
        tmp = tmp[1:]
        i+=1
      while tmp.endswith(SUFFIX_PUNCTUATIONS):
        src_tokenized[i] = tmp[:-1]
        src_tokenized.insert(i+1, tmp[-1])
        tmp = tmp[:-1]
        i+=1
      i+=1
    return src_tokenized
  
def tokenize(text: list, vocab: map, wordpiece=False):
  result = []
  for t in text:
    src_tokenized = split_tokens(t)
    src_tokenized = [x.encode('UTF-8') for x in src_tokenized]
    if wordpiece:
      words = []
      for i in range(len(src_tokenized)):
        words.extend(_nest_wp_tokenize(src_tokenized[i], vocab))
      src_tokenized = words
    src_indexed = [vocab.get(x, UNK_TOKEN) for x in src_tokenized]
    result.append([BOS_TOKEN, *src_indexed, EOS_TOKEN])

  if len(result) > 1:
    max_len = max([len(x) for x in result])
    for i in range(len(result)):
      result[i] += [PAD_TOKEN] * (max_len - len(result[i]))
  return torch.tensor(result), ['[BOS]', *[x if isinstance(x, str) else x.decode('UTF-8') for x in src_tokenized], '[EOS]']

def detokenize(text: torch.Tensor, vocab: list):
  result = []
  for t in text.cpu():
    dst_tokenized = [vocab[x] for x in t]
    dst_tokenized = [x if isinstance(x, str) else x.decode('utf8') for x in dst_tokenized]
    teks = []
    lastIsPrefix = False
    for token in dst_tokenized:
      if token in ['[BOS]', '[EOS]', '[PAD]', '[UNK]']:
        continue
      if token.startswith('_'):
        teks.append(token[1:])
      else:
        if not lastIsPrefix and token not in SUFFIX_PUNCTUATIONS:
          teks.append(' ')
        teks.append(token)
        lastIsPrefix = token in PREFIX_PUNCTUATIONS
    result.append(''.join(teks).strip())
  return result, dst_tokenized






