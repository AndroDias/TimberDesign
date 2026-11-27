import math

def floor_vibration(l,b,el,et,m,z,fw,level,joisted=True,two_way=False,multifamily=False,kred=.7,mures=.4):
    if min(l,b,el,et,m,z,fw)<=0 or not 1<=level<=8: raise ValueError('Parâmetros inválidos')
    ke=math.sqrt(1+(l/b)**4*et/el) if two_way else 1.
    f=ke*math.pi/(2*l*l)*math.sqrt(el/m)
    fl=max(4*fw,8 if multifamily or level<=2 else 0)
    bef=min(.95*l*(et/el)**.25,b)
    w=1000*1000*l**3/(48*el*bef)
    modal=m*l*b/4
    impulse=42*fw**1.43/f**1.3
    v1=kred*impulse/(modal+70)
    ratio=b/l*(el/et)**.25
    ki=max(.48*ratio,1)
    eta=1.35-.4*ki if ki<=(1.9 if joisted else 1.7) else (.59 if joisted else .67)
    v=ki*v1*(.65-.01*f)*(1.22-11*z)*eta
    if .65-.01*f<=0 or 1.22-11*z<=0: raise ValueError('Expressão de velocidade fora do domínio físico; requer análise específica.')
    kr=max(.19*ratio,1)
    a=kr*mures*50/(math.sqrt(2)*2*z*modal) if f<fl else None
    wm=[.25,.25,.5,1,1.25,1.5,1.75,2][level-1]
    wl=wm if level<=3 else min(wm,max(wm*3.6/l,.5))
    vl=[.0004,.0008,.0012,.0016,.0024,.0036,.0042,.0048][level-1]
    checks={'Frequência':(4.5 if level<=4 else fl)/f,'Rigidez':w/wl,'Velocidade':v/vl}
    if a is not None and level<=4: checks['Aceleração']=a/([.02,.04,.06,.08][level-1])
    return dict(f=f,fl=fl,bef=bef,w=w,modal=modal,impulse=impulse,ki=ki,eta=eta,v=v,a=a,kr=kr,checks=checks,wl=wl,vl=vl)
