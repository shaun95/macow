__author__ = 'max'

import torch


def norm(p: torch.Tensor, dim: int):
    """Computes the norm over all dimensions except dim"""
    if dim is None:
        return p.norm()
    elif dim == 0:
        output_size = (p.size(0),) + (1,) * (p.dim() - 1)
        return p.contiguous().view(p.size(0), -1).norm(dim=1).view(*output_size)
    elif dim == p.dim() - 1:
        output_size = (1,) * (p.dim() - 1) + (p.size(-1),)
        return p.contiguous().view(-1, p.size(-1)).norm(dim=0).view(*output_size)
    else:
        return norm(p.transpose(0, dim), 0).transpose(0, dim)


def squeeze2d(x, factor=2):
    assert factor >= 1
    if factor == 1:
        return x
    batch, n_channels, height, width = x.size()
    assert height % factor == 0 and width % factor == 0
    # [batch, channels, height, width] -> [batch, channels, height/factor, factor, width/factor, factor]
    x = x.view(-1, n_channels, height // factor, factor, width // factor, factor)
    # [batch, channels, factor, factor, height/factor, width/factor]
    x = x.permute(0, 1, 3, 5, 2, 4).contiguous()
    # [batch, channels*factor*factor, height/factor, width/factor]
    x = x.view(-1, n_channels * factor * factor, height // factor, width // factor)
    # [2 * batch, channels*factor*factor/2, height/factor, width/factor)
    x = torch.cat(x.chunk(2, dim=1), dim=0)
    return x


def unsqueeze2d(x, factor=2):
    assert factor >= 1
    if factor == 1:
        return x
    # [2*batch, channels/2, heigh, weight] -> [batch, channels, height, weight]
    x = torch.cat(x.chunk(2, dim=0), dim=1)
    batch, n_channels, height, width = x.size()
    assert n_channels >= 4 and n_channels % 4 == 0
    # [batch, channels, height, width] -> [batch, channels/(factor*factor), factor, factor, height, width]
    x = x.view(-1, int(n_channels / factor ** 2), factor, factor, height, width)
    # [batch, channels/(factor*factor), height, factor, width, factor]
    x = x.permute(0, 1, 4, 2, 5, 3).contiguous()
    # [batch, channels/(factor*factor), height*factor, width*factor]
    x = x.view(-1, int(n_channels / factor ** 2), int(height * factor), int(width * factor))
    return x


def exponentialMovingAverage(original, shadow, decay_rate, init=False):
    params = dict()
    for name, param in shadow.named_parameters():
        params[name] = param
    for name, param in original.named_parameters():
        shadow_param = params[name]
        if init:
            shadow_param.data.copy_(param.data)
        else:
            shadow_param.data.add_((1 - decay_rate) * (param.data - shadow_param.data))


def logPlusOne(x):
    """
    compute log(x + 1) for small x
    Args:
        x: Tensor

    Returns: Tensor
        log(x+1)

    """
    eps=1e-4
    mask = x.abs().le(eps).type_as(x)
    return x.mul(x.mul(-0.5) + 1.0) * mask + (x + 1.0).log() * (1.0 - mask)
