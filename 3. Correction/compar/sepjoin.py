from collections import Counter
import unicodedata
import re
PREFIX_PUNCTUATIONS = tuple("{[(“=")
SUFFIX_PUNCTUATIONS = tuple("}])”.,;:?!=")


def cleanup(text: str):
    text = unicodedata.normalize('NFKD', text).lower().strip()
    # drop all latins
    text = re.sub(r'\[\S+\]', '', text)
    # drop all symbols
    text = re.sub(r'\{\w+\}', '', text)
    # drop all misc
    text = re.sub(r'ttg\.', '', text)
    # replace all new lines
    text = re.sub(r'\n+', ' ; ', text)

    return text


def split_tokens(text: str):
    src_tokenized = text.split()
    # split by punctuations
    i = 0
    while i < len(src_tokenized):
        tmp = src_tokenized[i]
        if tmp.startswith(PREFIX_PUNCTUATIONS):
            src_tokenized[i] = tmp[1:]
            src_tokenized.insert(i, tmp[0])
            tmp = tmp[1:]
            i += 1
        if tmp.endswith(SUFFIX_PUNCTUATIONS):
            src_tokenized[i] = tmp[:-1]
            src_tokenized.insert(i+1, tmp[-1])
            tmp = tmp[:-1]
            i += 1
        i += 1
    return src_tokenized


def part_mad_idr(text: list[str]):
    result_mad = []
    result_ind = []
    stack = []
    for t in text:
        # IND -> MAD (could be multiple.. we only switch if it last)
        if t == ';':
            result_ind.extend(stack)
            stack = []
        # MAD -> IND (should once)
        elif t == '=':
            result_mad.extend(stack)
            stack = []
        else:
            stack.append(t)
    result_ind.extend(stack)
    return result_mad, result_ind



# total in fix, same in both, diff in old
def countiitt(oldtt, fixtt):
    oldd = dict(Counter(oldtt))
    fixd = dict(Counter(fixtt))
    total, same, diffm, diffp = 0, 0, 0, 0
    for k in set(oldd.keys()) & set(fixd.keys()):
        if len(k) <= 1 and (k == "" or k in PREFIX_PUNCTUATIONS or k in SUFFIX_PUNCTUATIONS):
            continue
        if k in fixd:
            total += fixd[k]
            if k in oldd:
                same += min(fixd[k], oldd[k])
                if oldd[k] > fixd[k]:
                    diffm += oldd[k] - fixd[k]
                elif oldd[k] < fixd[k]:
                    diffp += fixd[k] - oldd[k]
            else:
                diffp += fixd[k]
        else:
            diffm += oldd[k]
    print(total, same, diffm, diffp)
    return total, same, diffm, diffp


oldf = open('cold.txt', 'r', encoding='utf8')
fixf = open('cfix.txt', 'r', encoding='utf8')
oldt = '\n'.join(oldf.readlines())
fixt = '\n'.join(fixf.readlines())
oldtt = split_tokens(cleanup(oldt))
fixtt = split_tokens(cleanup(fixt))
oldf.close()
fixf.close()

oldtm, oldti = part_mad_idr(oldtt)
fixtm, fixti = part_mad_idr(fixtt)

countiitt(oldtm, fixtm)
countiitt(oldti, fixti)