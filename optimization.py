import numpy as np
from beam import calcular_viga
from eurocode5 import resistencia
from serviceability import deformacoes

def pesquisar(larguras, alturas, *, L,E,G,rho,g,q,apoio,psi,mat,fm,fv,kp,km,gm,kvar,gg,gq,kd,psi1,psi2,w0,limite,nfin,nfreq,travada,flim,alim,dinamica=False,preco=0):
    rows=[]
    for b in sorted(set(larguras)):
        for h in sorted(set(alturas)):
            pp=b*h/1e6*rho*9.81/1000
            massa=(pp+g+psi*q)*1000/9.81
            u={}
            for nome,carga,k in [('G',gg*(pp+g),kp),('G+Q',gg*(pp+g)+gq*q,km if q else kp)]:
                r=calcular_viga(L,b,h,E,carga,apoio,massa)
                a=resistencia(mat,h,fm,fv,k,gm,kvar,r['sigma'],r['tau'],r['W'],travada=travada)
                for key in ('flexao','corte','instabilidade'):
                    if a[key] is not None: u[nome+' '+key]=a[key]
            d=deformacoes(L,b,h,E,G,pp+g,q,apoio,massa,kd,psi1,psi2,w0)
            for nome,comb,key,n in [('Instantânea','Característica','inst',limite),('Final característica','Característica','net',nfin),('Final frequente','Frequente','net',nfreq),('Final quase permanente','Quase permanente','net',nfin)]:
                u[nome]=float(np.max(np.abs(d[comb][key])))/(L*1000/n)
            if dinamica:
                u['Frequência indicativa']=flim/r['f']; u['Flexibilidade indicativa']=r['flex']/alim
            crit=max(u,key=u.get); util=u[crit]; vol=b*h/1e6*L
            rows.append({'b (mm)':b,'h (mm)':h,'Volume (m³)':vol,'Custo estimado (€)':vol*preco,'Utilização (%)':100*util,'Condicionante':crit,'f1 (Hz)':r['f'],'Estado':'Excede' if util>1 else ('Critérios calculados satisfeitos' if travada else 'Parcial — estabilidade pendente')})
    return rows
