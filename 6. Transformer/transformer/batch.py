from .utils import subsequent_mask
from torch import Tensor, int64
from torch.utils.data import DataLoader


class Batch:
    """Object for holding a batch of data with mask during training."""

    def __init__(self, src: Tensor, tgt=None, pad=2):  # 2 = <blank>
        self.src = src
        self.src_mask = (src != pad).unsqueeze(-2)
        if tgt is not None:
            self.tgt = tgt[:, :-1]
            self.tgt_y = tgt[:, 1:]
            self.tgt_mask = self.make_std_mask(self.tgt, pad)
            self.ntokens = (self.tgt_y != pad).data.sum()

    @staticmethod
    def make_std_mask(tgt, pad):
        "Create a mask to hide padding and future words."
        tgt_mask = (tgt != pad).unsqueeze(-2)
        tgt_mask = tgt_mask & subsequent_mask(tgt.size(-1)).type_as(
            tgt_mask.data
        )
        return tgt_mask


def data_gen(data: Tensor, batch_size):
    dataloader = DataLoader(data, batch_size=batch_size, shuffle=True)
    for data in dataloader:
        src = data[:,0]
        tgt = data[:,1].to(int64)
        batch = Batch(src, tgt, 2)
        yield batch