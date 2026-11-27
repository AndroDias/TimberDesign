import math
import numpy as np


def calcular_viga(L, b, h, E, q, apoio, massa):
    A = b*h
    I = b*h**3/12
    W = b*h**2/6
    EI = E*I/1e6  # N m²
    p = q*1000  # N/m
    x = np.linspace(0, L, 201)
    if apoio == 'Simplesmente apoiada':
        M = q*x*(L-x)/2
        V = q*(L/2-x)
        w = p*x*(L**3-2*L*x*x+x**3)/(24*EI)
        lam = math.pi
        flex = 1000*L**3/(48*EI)
    elif apoio == 'Bi-encastrada':
        M = q*(L*x/2-x*x/2-L*L/12)
        V = q*(L/2-x)
        w = p*x*x*(L-x)**2/(24*EI)
        lam = 4.7300407449
        flex = 1000*L**3/(192*EI)
    elif apoio == 'Consola':
        M = -q*(L-x)**2/2
        V = q*(L-x)
        w = p*x*x*(6*L*L-4*L*x+x*x)/(24*EI)
        lam = 1.8751040687
        flex = 1000*L**3/(3*EI)
    else:
        raise ValueError('Apoio inválido')
    mmax = float(max(abs(M)))
    vmax = float(max(abs(V)))
    return dict(A=A,I=I,W=W,M=mmax,V=vmax,sigma=mmax*1e6/W,tau=1.5*vmax*1000/A,delta=float(max(w))*1000,f=lam**2/(2*math.pi*L**2)*math.sqrt(EI/massa),flex=flex*1000,x=x,Mx=M,Vx=V,wx=w*1000)
