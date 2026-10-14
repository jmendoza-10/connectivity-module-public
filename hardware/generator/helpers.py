from engine import place, place_pin, snap, tw, G, SIDE
import math

def tip(it, key): t = it.tip(key); return t['x'], t['y']

def other_net(it, net):
    ns = [g['net'] for g in it.groups if g['net'] != net]
    return ns[0] if ns else net

def vpart(it, x, ytop, topnet=None, up=True):
    """2-pin part vertical; pin carrying `topnet` (default: non-GND / pin1) at top tip (x,ytop)."""
    if topnet is None:
        nets = [g['net'] for g in it.groups]
        topnet = nets[0] if nets[0] != 'GND' else nets[1]
    key = pinkey(it, topnet)
    place_pin(it, key, x, ytop, 'U')
    return it

def pinkey(it, net):
    for g in it.groups:
        if g['net'] == net: return g['pins'][0][0]
    raise KeyError(f'{it.ref} has no net {net}')

def hpart(it, xl, y, leftnet=None):
    if leftnet is None:
        leftnet = it.groups[0]['net']
    place_pin(it, pinkey(it, leftnet), xl, y, 'L')
    return it

def bot(it):
    return max(t['y'] for t in it.tips())
def right(it):
    return max(t['x'] for t in it.tips())

def fw(it):
    return max(tw(it.ref), tw(it.value))

def caprow(items, x0, ytop, dx=None, topnets=None):
    x = x0
    for i, it in enumerate(items):
        vpart(it, x, ytop, topnets[i] if topnets else None)
        step = dx or max(5.08, math.ceil((2.2 + fw(it) + 1.0) / 2.54) * 2.54)
        x += step
    return x

def vchain(items, x, ytop, gap=2.54):
    """stack vertical 2-pin parts; top net of each = shared net with previous."""
    y = ytop; prev = None
    for it in items:
        if prev is None:
            vpart(it, x, y)
        else:
            shared = ({g['net'] for g in prev.groups} & {g['net'] for g in it.groups})
            sh = [n for n in [g['net'] for g in prev.groups] if n in shared and n != 'GND']
            vpart(it, x, y, sh[-1] if sh else None)
        y = bot(it) + gap; prev = it
    return y

def hchain(items, xl, y, gap=2.54):
    x = xl; prev = None
    for it in items:
        if prev is None: hpart(it, x, y)
        else:
            shared = ({g['net'] for g in prev.groups} & {g['net'] for g in it.groups})
            hpart(it, x, y, sorted(shared)[0] if shared else None)
        x = right(it) + gap; prev = it
    return x
