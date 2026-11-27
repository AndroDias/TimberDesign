import math

def lineares(g,q,s=None):
    if not all(math.isfinite(x) and x>=0 for x in (g,q)) or (s is not None and (not math.isfinite(s) or s<=0)):
        raise ValueError('Cargas ou afastamento inválidos.')
    return g*(1 if s is None else s),q*(1 if s is None else s)
