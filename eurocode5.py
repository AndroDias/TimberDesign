DURACOES = ['Permanente','Longa','Média','Curta','Instantânea']

def coeficientes(material, sc, duracao, madeira_verde=False):
    kmod = ([.6,.7,.8,.9,1.1] if sc in (1,2) else [.55,.6,.7,.8,1.0])[DURACOES.index(duracao)]
    kdef = {1:.6,2:.8,3:2.0}[sc] + int(madeira_verde)
    return kmod,kdef,1.25 if material.startswith('GL') else 1.30

def combinacoes(g,q,gamma_g,gamma_q,psi1,psi2):
    return {'ELU — permanente':gamma_g*g,'ELU — permanente + variável':gamma_g*g+gamma_q*q,'ELS — característica':g+q,'ELS — frequente':g+psi1*q,'ELS — quase permanente':g+psi2*q}


def resistencia(mat,h,fm,fv,kmod,gamma,kvar,sigma,tau,W,mcr=None,beta_m=0.,beta_theta=0.,travada=False):
    import math
    gl=mat.startswith('GL')
    # 5.3(2): no enhancement below reference depth
    khm=(max(h,600)/600)**(-.04) if gl else 1.0
    khv=max(.9,min(1.1,(max(h,600)/600)**(-.1))) if gl else 1.0
    kv=min(1.,khv*kvar*(2.75 if gl else 2.30)/fv)
    fmd=kmod*khm*fm/gamma
    fvd=kmod*fv/gamma
    lam=km=ult=None
    if travada:
        km=1.
    elif mcr is not None and mcr>0:
        lam=math.sqrt(fm*W/(mcr*1e6))
        if lam<=.55: km=1.
        else:
            phi=.5*(1+beta_theta+beta_m*(lam-.55)+lam**2)
            km=min(1.,1/(phi+math.sqrt(max(0.,phi**2-lam**2))))
    if km is not None: ult=sigma/(km*fmd)
    return dict(khm=khm,khv=khv,kv=kv,fmd=fmd,fvd=fvd,flexao=sigma/fmd,corte=tau/(kv*fvd),lam=lam,km=km,instabilidade=ult)


def compressao_apoio(R,b,l,fc90,kmod,gamma):
    # EC5 8.1.6.1 (1)-(4): kmat = kc90 = 1, sem benefício de dispersão.
    if min(b,l,fc90,kmod,gamma)<=0 or R<0: raise ValueError('Dados de apoio inválidos')
    sigma=R*1000/(b*l)
    fd=kmod*fc90/gamma
    return dict(sigma=sigma,fd=fd,util=sigma/fd)
