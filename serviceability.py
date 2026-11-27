import numpy as np
from beam import calcular_viga

def deformacoes(L,b,h,E,G,g,q,apoio,massa,kdef,psi1,psi2,w0):
    r=calcular_viga(L,b,h,E,1.,apoio,massa)
    x=r['x']; A=b*h
    # Timoshenko: rectangular section, shear correction 5/6.
    s=(x*(2*L-x)/2 if apoio=='Consola' else x*(L-x)/2)*1e6/(5/6*G*A)
    f=r['wx']; shape=(x/L)**2 if apoio=='Consola' else 4*x*(L-x)/L**2
    out={}
    for name,p in [('Característica',1.),('Frequente',psi1),('Quase permanente',psi2)]:
        a=g+psi2*q; c=(p-psi2)*q
        w1=(f+s)*a; w2=w1*kdef; w3=(f+s)*c
        total=w1+w2+w3; net=total-w0*shape
        out[name]=dict(x=x,flexao=f*(g+p*q),corte=s*(g+p*q),inst=w1+w3,w1=w1,w2=w2,w3=w3,total=total,net=net)
    return out
