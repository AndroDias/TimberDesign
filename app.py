import streamlit as st
import plotly.graph_objects as go
from beam import calcular_viga
from cargas import lineares
from serviceability import deformacoes
import numpy as np
from eurocode5 import coeficientes, combinacoes, DURACOES, resistencia

st.set_page_config(page_title='TimberDesign',layout='wide')
st.markdown("""<style>
[data-testid="stMetric"] {background:#e0edfa;color:#24578d;padding:12px;border-radius:7px;}
[data-testid="stMetric"] * {color:#24578d !important;}
[data-testid="stNumberInput"] input:disabled {background:#e0edfa !important;color:#24578d !important;-webkit-text-fill-color:#24578d !important;}
</style>""",unsafe_allow_html=True)
st.caption('Campos editáveis: fundo normal | Azul-claro: valores automáticos | Verde/vermelho: resultado | Amarelo: pendente')
st.title('TimberDesign')
st.warning('V1.1 Beta — acesso de teste. Auditoria parcial; não utilizar para decisões de projeto nem como declaração de conformidade regulamentar.')
st.subheader('Pré-dimensionamento de vigas de madeira')
st.caption('V1.1 Beta — Resistência, deformações e vibrações EN 1995-1-1:2025')
with st.sidebar:
    st.header('Dados de entrada')
    apoio=st.selectbox('Condições de apoio',['Simplesmente apoiada','Bi-encastrada','Consola'],help='Modelo idealizado: apoio simples permite rotação; encastramento impede rotação; consola tem uma extremidade livre.')
    L=st.number_input('Vão (m)',0.5,30.,5.,0.1,help='Distância entre apoios ou comprimento livre da consola.')
    b=st.number_input('Largura (mm)',20,1000,100,10,help='Dimensão horizontal da secção retangular.')
    h=st.number_input('Altura (mm)',40,2000,240,10,help='Dimensão vertical da secção, na direção da carga.')
    materiais={'C18':(9000,380),'C24':(11000,420),'C30':(12000,460),'GL24h':(11500,420),'GL28h':(12600,460),'GL32h':(14200,490)}
    mat=st.selectbox('Classe de resistência',list(materiais),index=3,help='Classe resistente do produto estrutural; confirmar na declaração de desempenho (DoP).')
    E,rho0=materiais[mat]
    override_rho=st.checkbox('Substituir massa volúmica de referência',help='Ativar para introduzir a massa volúmica real do produto.')
    rho=st.number_input('Massa volúmica adotada (kg/m³)',100.,1500.,float(rho0),10.,key='rho_'+mat+str(override_rho),disabled=not override_rho,help='Massa por unidade de volume, usada no peso próprio e massa dinâmica.')
    if not override_rho: rho=rho0
    st.caption('Valor inicial indicativo; ajustar ao produto e teor de água.')
    modo=st.radio('Tipo de carregamento',['Linear (kN/m)','Superficial (kN/m²)'],help='Carga superficial para vigas interiores de pavimentos unidirecionais com entre-eixos regular; carga linear para vigas isoladas ou largura tributária já considerada.')
    area=modo.startswith('Superficial')
    entre=st.number_input('Entre-eixos das vigas (mm)',50,3000,600,25,help='Distância entre eixos, igual à largura tributária de uma viga interior com espaçamento regular.')/1000 if area else None
    unidade='kN/m²' if area else 'kN/m'
    ge=st.number_input(f'Permanentes adicionais ({unidade})',0.,100.,1.,0.1,key='g_'+modo,help='Carga permanente característica, excluindo o peso próprio das vigas.')
    qe=st.number_input(f'Variáveis ({unidade})',0.,100.,1.,0.1,key='q_'+modo,help='Sobrecarga característica descendente, antes de majoração.')
    g,q=lineares(ge,qe,entre)
    st.metric('Permanente linear sem viga (kN/m)',f'{g:.3f}')
    st.metric('Variável linear (kN/m)',f'{q:.3f}')
    if area and b/1000>=entre: st.error('Entre-eixos deve ser superior à largura da viga.'); st.stop()
    st.subheader('Parâmetros regulamentares')
    sc=st.selectbox('Classe de serviço',[1,2,3],help='Classe de serviço associada à exposição à humidade: 1 interior seco, 2 protegido com maior humidade, 3 condições mais húmidas. Confirmar EC5.')
    dur=st.selectbox('Duração da ação variável',DURACOES,index=2,help='Classe de duração da ação variável que determina kmod.')
    verde=st.checkbox('Madeira maciça instalada próximo da saturação e seca sob carga',help='Condição especial de secagem sob carga que aumenta a fluência.') if not mat.startswith('GL') else False
    km,kd,gm0=coeficientes(mat,sc,dur,verde)
    override_gm=st.checkbox('Substituir γM automático',help='Permite introduzir um coeficiente diferente do valor de referência; confirmar Anexo Nacional.')
    gm=st.number_input('γM (Tabela 4.3, editável)',1.0,2.0,gm0,0.05,disabled=not override_gm,key='gm_'+mat+str(override_gm),help='Coeficiente parcial da resistência do material.')
    if not override_gm: gm=gm0
    gg=st.number_input('γG desfavorável (provisório)',1.0,2.0,1.35,0.05,help='Coeficiente parcial da ação permanente desfavorável. Confirmar EN 1990 e Anexo Nacional.')
    gq=st.number_input('γQ (provisório)',1.0,2.0,1.50,0.05,help='Coeficiente parcial da ação variável desfavorável.')
    psi1=st.number_input('ψ1 (provisório)',0.,1.,0.5,0.05,help='Fator de combinação frequente da ação variável.')
    psi2=st.number_input('ψ2 (provisório)',0.,1.,0.3,0.05,help='Fator quase permanente da ação variável, utilizado também na fluência.')
    psi=st.number_input('Fração da carga variável na massa dinâmica',0.,1.,0.3,0.05,help='Parcela da carga variável convertida em massa participante na vibração.')
    st.caption('Hipótese de massa participante a validar pelo engenheiro.')
    limite=st.number_input('Limite indicativo de flecha L/n',100,1000,300,50,help='Denominador n do limite de flecha L/n; referência escolhida pelo projetista.')
    flim=st.number_input('Frequência de referência (Hz)',1.,30.,8.,0.5,help='Frequência mínima indicativa para triagem dinâmica, não critério regulamentar isolado.')
    alim=st.number_input('Flexibilidade de referência (mm/kN)',0.1,10.,1.5,0.1,help='Flexibilidade máxima indicativa sob força pontual unitária.')
    st.subheader('Deformações — ELS')
    override_E=st.checkbox('Substituir módulo E de referência',help='Ativar para introduzir o módulo médio declarado pelo fabricante.')
    E=st.number_input('E0,mean (MPa)',100.,50000.,float(E),100.,key='E_'+mat+str(override_E),disabled=not override_E,help='Módulo médio de elasticidade paralelo ao fio, utilizado na rigidez à flexão EI. Confirmar DoP.')
    override_G=st.checkbox('Substituir módulo G de referência',help='Ativar para introduzir o módulo de distorção declarado pelo fabricante.')
    G=st.number_input('Gmean (MPa)',10.,5000.,650. if mat.startswith('GL') else 690.,10.,key='G_'+mat+str(override_G),disabled=not override_G,help='Módulo médio de distorção; controla a deformação por esforço transverso. Valor inicial indicativo, confirmar DoP.')
    w0=st.number_input('Contraflecha w0 (mm)',0.,500.,0.,0.5,help='Elevação inicial sem carga, a meio vão ou na ponta da consola. Perfil parabólico ou quadrático idealizado.')
    nfin=st.number_input('Limite final L/n',100,1000,250,25,help='Limite escolhido pelo projetista para a flecha líquida final; não é um valor universal do EC5.')
    nfreq=st.number_input('Limite frequente L/n',100,1000,300,25,help='Limite escolhido para deformação líquida da combinação frequente, incluindo fluência.')
    st.subheader('Resistência e estabilidade')
    fm=st.number_input('fm,k (MPa) — confirmar na DoP',1.,100.,float(mat[2:-1] if mat.startswith('GL') else mat[1:]),0.5,key='fm_'+mat,help='Resistência característica à flexão paralela ao fio.')
    fv=st.number_input('fv,k (MPa) — confirmar na DoP',0.1,20.,3.5 if mat.startswith('GL') else 4.,0.1,key='fv_'+mat,help='Resistência característica ao corte.')
    kvar=st.number_input('kvar — condições de humidade (8.1.11.1)',0.05,1.,1.,0.05,help='Fator de resistência ao corte associado à variação de humidade; confirmar condições do artigo 8.1.11.1.')
    travada=st.checkbox('Bordo comprimido integralmente travado por sistema rígido (todos os troços)',help='Confirmar travamento efetivo do bordo comprimido em todos os troços, incluindo zonas de momento negativo.')
    externo=st.checkbox('Introduzir momento crítico e imperfeições de análise externa',help='Utilizar parâmetros de uma análise de estabilidade independente validada.') if not travada else False
    mcr=beta_m=beta_theta=None
    if externo:
        mcr=st.number_input('My,cr (kNm)',0.001,100000.,20.,0.1,help='Momento crítico elástico de instabilidade lateral.')
        beta_m=st.number_input('βm — Tabela 8.2',0.,100.,0.1,0.01,help='Parâmetro de imperfeição de flexão da Tabela 8.2.')
        beta_theta=st.number_input('βθ — Tabela 8.2',0.,100.,0.1,0.01,help='Parâmetro de imperfeição de torção da Tabela 8.2.')
        st.caption('Valores iniciais ilustrativos: substituir por resultados validados de análise de estabilidade.')
    st.caption('Propriedades iniciais indicativas, não base de dados certificada. GL: lamelas paralelas ao eixo de flexão; ST: densidade característica ≤ 700 kg/m³.')
    bearing=st.checkbox('Avaliar compressão perpendicular nos apoios',help='Apenas apoios simples com contacto direto, retangular e uniforme em toda a largura da viga.') if apoio=='Simplesmente apoiada' else False
    la=st.number_input('Comprimento de apoio (mm)',1.,2000.,100.,1.,help='Comprimento efetivo de contacto paralelo ao fio; adota-se o menor dos dois apoios.') if bearing else None
    fc90=st.number_input('fc,90,k (MPa)',0.1,20.,2.5,0.1,help='Resistência característica perpendicular ao fio; confirmar na DoP.') if bearing else None
pp=b*h/1e6*rho*9.81/1000
massa=(pp+g+psi*q)*1000/9.81
r=calcular_viga(L,b,h,E,pp+g+q,apoio,massa)
st.write(f'**{apoio}** | {mat} | {b} × {h} mm | L = {L:.2f} m')
st.caption(f'Peso próprio: {pp:.3f} kN/m | Carga total não majorada: {pp+g+q:.3f} kN/m')
fig=go.Figure()
fig.add_scatter(x=[0,L],y=[0,0],mode='lines',line=dict(width=12,color='#b58a60'),showlegend=False)
for i in range(11):
    xx=L*i/10
    fig.add_annotation(x=xx,y=0.08,ax=xx,ay=0.7,axref='x',ayref='y',text='',showarrow=True,arrowhead=2)
if apoio=='Simplesmente apoiada':
    fig.add_scatter(x=[0,L],y=[-0.12,-0.12],mode='markers',marker=dict(symbol='triangle-up',size=20),showlegend=False)
else:
    for xx in ([0,L] if apoio=='Bi-encastrada' else [0]):
        fig.add_shape(type='line',x0=xx,x1=xx,y0=-0.3,y1=0.3,line=dict(width=7))
fig.update_layout(height=220,margin=dict(l=20,r=20,t=10,b=30),xaxis_title='x (m)',yaxis=dict(visible=False,range=[-0.4,1]),showlegend=False)
st.plotly_chart(fig,use_container_width=True)
st.header('Propriedades da secção')
for c,(n,v) in zip(st.columns(3),[('Área (mm²)',r['A']),('Inércia (mm⁴)',r['I']),('Módulo resistente (mm³)',r['W'])]): c.metric(n,f'{v:,.0f}')
st.header('Análise estática — cargas não majoradas')
for c,(n,v) in zip(st.columns(4),[('|M| máximo (kNm)',r['M']),('|V| máximo (kN)',r['V']),('Flexão (MPa)',r['sigma']),('Corte elástico bruto (MPa)',r['tau'])]): c.metric(n,f'{v:.2f}')
c1,c2=st.columns(2)
c1.metric('Flecha instantânea por flexão (mm)',f"{r['delta']:.2f}")
c2.metric('Limite indicativo (mm)',f'{L*1000/limite:.2f}')
st.header('Coeficientes e combinações')
st.caption('EN 1995-1-1:2025, Tabelas 4.3, 5.4 e 5.5. Parâmetros nacionais e EN 1990 por confirmar.')
kp=coeficientes(mat,sc,'Permanente',verde)[0]
for c,(n,v) in zip(st.columns(4),[('kmod permanente',kp),('kmod G+Q',km if q else kp),('kdef',kd),('γM',gm)]): c.metric(n,f'{v:.2f}')
rows=[]
for nome,carga in combinacoes(pp+g,q,gg,gq,psi1,psi2).items():
    rr=calcular_viga(L,b,h,E,carga,apoio,massa)
    rows.append({'Combinação':nome,'q (kN/m)':round(carga,3),'|M| (kNm)':round(rr['M'],3),'|V| (kN)':round(rr['V'],3),'Flecha elástica (mm)':round(rr['delta'],3) if nome.startswith('ELS') else None})
st.dataframe(rows,hide_index=True,use_container_width=True)
if psi2>psi1:
    st.error('Rever coeficientes: ψ2 superior a ψ1.')
    st.stop()
st.header('ELS — Deformações (EC5:2025, 9.2.2)')
st.caption('Equações 9.1–9.6. Limites editáveis de projeto; EN 1990:2023 e Anexo Nacional por confirmar.')
res=deformacoes(L,b,h,E,G,pp+g,q,apoio,massa,kd,psi1,psi2,w0)
rows=[]
for nome,d in res.items():
    peak=lambda k: float(np.max(d[k]))
    rows.append({'Combinação':nome,'Flexão inst. (mm)':peak('flexao'),'Corte inst. (mm)':peak('corte'),'w1 (mm)':peak('w1'),'w2 (mm)':peak('w2'),'w3 (mm)':peak('w3'),'wtot (mm)':peak('total'),'wmax (mm)':peak('net')})
st.dataframe(rows,hide_index=True,use_container_width=True)
for label,d,k,n in [('Instantânea característica',res['Característica'],'inst',limite),('Final característica líquida',res['Característica'],'net',nfin),('Final frequente líquida',res['Frequente'],'net',nfreq),('Final quase permanente líquida',res['Quase permanente'],'net',nfin)]:
    val=float(np.max(np.abs(d[k]))); lim=L*1000/n; u=val/lim
    (st.success if u<=1 else st.error)(f'{label}: {val:.2f} mm / {lim:.2f} mm — {100*u:.1f}%')
    st.progress(min(1.,u))
    if u>1: st.warning('Excede o limite de projeto adotado.')
fig=go.Figure()
for nome,d in res.items():
    fig.add_scatter(x=d['x'],y=d['net'],name=nome)
fig.update_layout(title='Deformação líquida final (mm)',xaxis_title='x (m)',yaxis_title='mm')
fig.update_yaxes(autorange='reversed')
st.plotly_chart(fig,use_container_width=True)
st.caption('w1: parcela elástica quase permanente; w2: fluência; w3: parcela elástica restante; wtot: soma; wmax: descontada a contraflecha. Verificações usam valor absoluto máximo ao longo da viga.')
st.header('ELU — resistência da secção e estabilidade')
st.caption('EC5:2025 — 5.3, 8.1.8.1, 8.1.11.1 e 8.2.2.3. Sem redução do esforço transverso junto aos apoios.')
checks=[]
bearing_report=[]
for nome,carga in combinacoes(pp+g,q,gg,gq,psi1,psi2).items():
    if not nome.startswith('ELU'): continue
    rr=calcular_viga(L,b,h,E,carga,apoio,massa)
    k=kp if nome=='ELU — permanente' or not q else km
    a=resistencia(mat,h,fm,fv,k,gm,kvar,rr['sigma'],rr['tau'],rr['W'],mcr,beta_m or 0.,beta_theta or 0.,travada)
    if bearing:
        from eurocode5 import compressao_apoio
        c90=compressao_apoio(rr['V'],b,la,fc90,k,gm)
        bearing_report.append((nome,f"{c90['sigma']:.3f} / {c90['fd']:.3f} MPa | {100*c90['util']:.2f}%"))
        a['apoio']=c90['util']
    checks.append((nome,a))
    with st.expander(nome,expanded=True):
        st.write(f"kmod = {k:.2f} | kh,m = {a['khm']:.3f} | kh,v = {a['khv']:.3f} | kv = {a['kv']:.3f}")
        st.write(f"fm,d = {a['fmd']:.3f} MPa | kv fv,d = {a['kv']*a['fvd']:.3f} MPa")
        for label,key in [('Flexão','flexao'),('Corte','corte'),('Instabilidade lateral','instabilidade'),('Compressão perpendicular','apoio')]:
            u=a.get(key)
            if u is None: st.warning(label+': não avaliada'); continue
            (st.success if u<=1 else st.error)(f'{label}: {100*u:.1f}% — '+('dentro do limite' if u<=1 else 'excede o limite'))
            st.progress(min(1.,u))
        if a['lam'] is not None: st.write(f"λm,rel = {a['lam']:.3f} | km = {a['km']:.3f}")
vals=[(a[k],n,k) for n,a in checks for k in ('flexao','corte','instabilidade','apoio') if a.get(k) is not None]
u,n,k=max(vals)
st.metric('Maior utilização entre verificações calculadas',f'{100*u:.1f}%')
st.caption(f'{n} — {k}. Não representa conformidade global.')
st.warning('Compressão perpendicular limitada a apoios simples; ligações, fogo e validação do Anexo Nacional ainda pendentes. Instabilidade depende de travamento confirmado ou análise externa válida.')
st.header('Diagramas')
for titulo,k,un in [('Momento fletor','Mx','kNm'),('Esforço transverso','Vx','kN'),('Deformação por flexão','wx','mm')]:
    fig=go.Figure(go.Scatter(x=r['x'],y=r[k],fill='tozeroy',mode='lines'))
    fig.update_layout(title=titulo,xaxis_title='x (m)',yaxis_title=un,height=270,margin=dict(l=40,r=20,t=45,b=40))
    if k=='wx': fig.update_yaxes(autorange='reversed')
    st.plotly_chart(fig,use_container_width=True)
st.header('ELS — análise preliminar de vibrações')
c1,c2,c3=st.columns(3)
c1.metric('Massa linear (kg/m)',f'{massa:.2f}')
c2.metric('Frequência fundamental (Hz)',f"{r['f']:.2f}")
c3.metric('Flexibilidade (mm/kN)',f"{r['flex']:.3f}")
st.write('Frequência: '+('atinge' if r['f']>=flim else 'não atinge')+' a referência adotada.')
st.write('Flexibilidade: '+('dentro' if r['flex']<=alim else 'fora')+' da referência adotada.')
st.caption('Força pontual a meio vão ou na extremidade livre da consola. Referências editáveis, não critérios universais de conformidade.')
st.warning('Protótipo não validado para projeto. Apoios ideais, secção constante, massa uniforme e teoria de Euler-Bernoulli. Inclui combinações preliminares e fluência por flexão e corte nos ELS estáticos. A análise dinâmica continua Euler-Bernoulli. A triagem da viga não avalia resposta impulsiva nem comportamento global do pavimento.')

floor_report=[]
from vibrations import floor_vibration
st.header('ELS — Vibrações do pavimento (EC5:2025, 9.3.2)')
st.caption('Método simplificado para pavimento retangular de um vão, apoios articulados rígidos, rigidez transversal uniforme e carga predominantemente uniforme. Independente do modelo de viga acima.')
if st.checkbox('Ativar análise de pavimento',help='Avalia o pavimento completo de uma divisão, não uma viga isolada.'):
    cat=st.selectbox('Categoria de utilização',['A — Moradia','A — Multifamiliar','B — Escritório','C1','C3','D'],help='Categorias abrangidas por 9.3.1(3); não inclui multidões, exercício físico ou máquinas.')
    lev=st.selectbox('Nível de desempenho',[1,2,3,4,5,6,7,8],index=4,format_func=lambda n:['I','II','III','IV','V','VI','VII','VIII'][n-1],help='Tabela 9.1; I é o mais exigente. Tabela 9.2 recomenda nível V para moradias, IV–V para multifamiliar e III para escritórios (escolha standard). Confirmar Anexo Nacional.')
    c1,c2=st.columns(2)
    with c1:
        lp=st.number_input('Vão do pavimento (m)',.5,30.,float(L),.1,help='Distância entre apoios rígidos do pavimento.')
        bp=st.number_input('Largura do pavimento (m)',.5,50.,4.,.1,help='Dimensão transversal da divisão considerada.')
        gp=ge+pp/entre if area else st.number_input('Permanentes totais (kN/m²)',.01,30.,1.5,.1,help='Inclui vigas, revestimentos, teto, elementos suspensos e divisórias. Não adicionar peso próprio novamente.')
        qp=qe if area else st.number_input('Sobrecarga característica (kN/m²)',0.,30.,2.,.1,help='Carga de utilização; 10% entra na massa dinâmica segundo 9.3.1.2.')
        if area:
            st.metric('Permanentes totais (kN/m²)',f'{gp:.3f}')
            st.metric('Sobrecarga (kN/m²)',f'{qp:.3f}')
        tipo=st.selectbox('Tipo de pavimento',['Vigado','Vigado com piso flutuante','Laje / nervurado / misto','Laje / nervurado / misto com piso flutuante'],help='Tipologia que determina amortecimento de referência e fator eta.')
        z=st.number_input('Amortecimento ζ (%)',.1,10.,[2.,3.,2.5,4.][['Vigado','Vigado com piso flutuante','Laje / nervurado / misto','Laje / nervurado / misto com piso flutuante'].index(tipo)],.1,key='z_'+tipo,help='Percentagem de amortecimento crítico; valores iniciais de 9.3.1.1.')/100
    with c2:
        s=entre if area else st.number_input('Espaçamento entre vigas (m)',.05,3.,.6,.05,help='Distância entre eixos para estimar EI longitudinal.')
        if area: st.metric('Entre-eixos adotado (m)',f'{s:.3f}')
        est=E*1e6*(b/1000)*(h/1000)**3/12/s/1e6
        st.caption(f'EI longitudinal por metro, só flexão das vigas: {est:.4f} MN·m²/m. Corrigir para corte, deslizamento e restantes camadas.')
        el=st.number_input('EI longitudinal aparente (MN·m²/m)',.00001,10000.,float(est),.01,format='%.5f',help='Rigidez efetiva por metro de largura incluindo corte e deslizamento; confirmar por análise independente (9.3.1.3).')*1e6
        et=st.number_input('EI transversal aparente (MN·m²/m)',.00001,10000.,.05,.01,format='%.5f',help='Rigidez transversal efetiva por metro; valor inicial ilustrativo, substituir por cálculo do pavimento.')*1e6
        tw=st.checkbox('Pavimento apoiado em quatro bordos, bidirecional',help='Ativa ke,2 da equação 9.14; desativado para vão unidirecional.')
        longwalk=st.checkbox('Percurso livre superior a 10 m',help='Percursos longos podem aumentar frequência de marcha e acumulação ressonante.')
        fwmin=1.5 if cat.startswith('A') else 2.
        fw=st.number_input('Frequência de marcha (Hz)',fwmin,4.,2.5 if longwalk else fwmin,.1,key='fw_'+cat+str(longwalk),help='9.3.1.4: pelo menos 1,5 Hz residencial e 2 Hz restantes categorias; 2,5 Hz possível em percursos longos.')
        kred=st.number_input('kred',.7,1.,.7,.05,help='Redução por distância entre pessoa que caminha e recetor; 1 para coincidência (9.22).')
        mu=st.number_input('μres',.8 if longwalk else .4,1.,.8 if longwalk else .4,.05,key='mu_'+str(longwalk),help='Fator de acumulação ressonante; pelo menos 0,8 razoável para percursos livres superiores a 10 m (9.28).')
    confirmed=st.checkbox('Confirmo âmbito do método e rigidezes aparentes introduzidas',help='Confirmar geometria, apoios rígidos, distribuição de massa, rigidezes e ausência de aberturas relevantes. Valores iniciais não constituem validação.')
    try:
        mp=(gp+.1*qp)*1000/9.81
        v=floor_vibration(lp,bp,el,et,mp,z,fw,lev,tipo.startswith('Vigado'),tw,cat=='A — Multifamiliar',kred,mu)
        floor_report=[('Categoria / nível',f'{cat} / {lev}'),('Âmbito confirmado',str(confirmed)),('Vão / largura (m)',f'{lp} / {bp}'),('Gk / Qk (kN/m²)',f'{gp} / {qp}'),('EI longitudinal / transversal (N m²/m)',f'{el} / {et}'),('Amortecimento / marcha',f'{z*100:.2f}% / {fw} Hz'),('kred / μres',f'{kred} / {mu}'),('Tipo / quatro bordos',f'{tipo} / {tw}'),('Massa superficial (kg/m²)',f'{mp:.3f}'),('Frequência (Hz)',f"{v['f']:.3f}"),('Flecha 1 kN (mm)',f"{v['w']:.3f}"),('Velocidade RMS (mm/s)',f"{v['v']*1000:.3f}"),('Aceleração RMS (m/s²)',str(v['a']))]+[(k,f'{100*u:.2f}%') for k,u in v['checks'].items()]
        for c,(label,val) in zip(st.columns(4),[('Massa (kg/m²)',mp),('f1 (Hz)',v['f']),('f1,lim (Hz)',v['fl']),('w1kN (mm)',v['w'])]): c.metric(label,f'{val:.3f}')
        st.write('Resposta: '+('ressonante' if v['f']<v['fl'] else 'transitória'))
        st.write(f"Velocidade RMS: {v['v']*1000:.3f} mm/s; limite {v['vl']*1000:.3f} mm/s")
        if v['a'] is not None: st.write(f"Aceleração RMS: {v['a']:.4f} m/s²")
        for label,u in v['checks'].items():
            st.write(f'{label}: {100*u:.1f}%'); st.progress(min(1.,u))
        if not confirmed: st.warning('Resultados ilustrativos: confirmar dados e âmbito antes de interpretar.')
        elif max(v['checks'].values())>1: st.error('Excede pelo menos um critério do nível selecionado.')
        else: st.success('Satisfaz os critérios calculados do nível selecionado; não constitui validação global.')
        with st.expander('Resultados intermédios e referências'):
            st.write({k:round(v[k],5) for k in ['bef','modal','impulse','ki','eta','kr','wl']})
            st.caption('Equações 9.12–9.14, 9.17–9.18 e 9.21–9.29; Tabelas 9.1 e 9.2. Massa modal simplificada mlb/4.')
    except ValueError as e: st.error(str(e))
    st.warning('Não inclui método geral do Anexo E, dois vãos, apoios flexíveis, reforço transversal discreto, multidões ou máquinas. Anexo Nacional por confirmar.')


optimization_report=[]
from optimization import pesquisar
st.header('Pré-dimensionamento automático — V1.1 Beta')
st.caption('Utiliza os parâmetros atuais da viga. A pesquisa não altera a secção manual nem verifica o pavimento completo.')
with st.expander('Configurar pesquisa de secções',expanded=True):
    ls=st.text_input('Larguras candidatas (mm)','60, 80, 100, 120, 140, 160, 180, 200, 240',help='Lista separada por vírgulas. Confirmar disponibilidade comercial com o fornecedor.')
    hs=st.text_input('Alturas candidatas (mm)','120, 160, 200, 240, 280, 320, 360, 400, 440, 480, 520, 600',help='Lista de alturas de secções retangulares, separada por vírgulas.')
    preco=st.number_input('Preço indicativo (€/m³)',0.,10000.,0.,50.,help='Preço unitário da madeira, sem ligações, transporte ou montagem. Zero significa não estimar custo.')
    dinamica=st.checkbox('Incluir triagem dinâmica da viga isolada',help='Aplica os limites indicativos de frequência e flexibilidade da viga; não substitui a verificação do pavimento.')
    esp=st.text_input('Entre-eixos candidatos (mm)',str(round(entre*1000)),help='Lista de afastamentos separados por vírgulas; verificar revestimento e travamentos para cada opção.') if area else ''
    ordem=st.selectbox('Ordenar por',(['Madeira (m³/m²)','Utilização (%)','Custo madeira (€/m²)'] if area else ['Volume (m³)','Utilização (%)','Custo estimado (€)']),help='Ordenação crescente das soluções que satisfazem os critérios calculados.')
    if st.checkbox('Executar pesquisa',help='Ativa a pesquisa e recalcula quando os parâmetros são alterados.'):
        try:
            larguras=sorted(set(int(x.strip()) for x in ls.split(','))); alturas=sorted(set(int(x.strip()) for x in hs.split(',')))
            if not all(20<=x<=1000 for x in larguras) or not all(40<=x<=2000 for x in alturas) or len(larguras)*len(alturas)>2500: raise ValueError('Dimensões fora dos limites ou mais de 2500 combinações.')
            espacamentos=sorted(set(int(x.strip())/1000 for x in esp.split(','))) if area else [None]
            if area and (not all(.05<=x<=3 for x in espacamentos) or len(larguras)*len(alturas)*len(espacamentos)>2500): raise ValueError('Afastamentos inválidos ou mais de 2500 combinações.')
            rows=pesquisar(larguras,alturas,L=L,E=E,G=G,rho=rho,g=g,q=q,apoio=apoio,psi=psi,mat=mat,fm=fm,fv=fv,kp=kp,km=km,gm=gm,kvar=kvar,gg=gg,gq=gq,kd=kd,psi1=psi1,psi2=psi2,w0=w0,limite=limite,nfin=nfin,nfreq=nfreq,travada=travada,flim=flim,alim=alim,dinamica=dinamica,preco=preco,espacamentos=espacamentos,g_area=ge if area else None,q_area=qe if area else None)
            import pandas as pd
            if not rows: raise ValueError('Nenhuma geometria válida: verificar larguras e afastamentos.')
            df=pd.DataFrame(rows); ok=df[df['Utilização (%)']<=100].sort_values([ordem,('Madeira (m³/m²)' if area else 'Volume (m³)')] if ordem not in ('Volume (m³)','Madeira (m³/m²)') else [ordem,'Utilização (%)'])
            optimization_report=[('Pesquisa',f'{len(ok)} / {len(df)} candidatas dentro dos critérios'),('Ordenação',ordem),('Travamento confirmado',str(travada)),('Triagem dinâmica',str(dinamica)),('Larguras / alturas (mm)',f'{ls} / {hs}')]+[(f"{int(t['b (mm)'])} x {int(t['h (mm)'])} mm",f"Utilização {t['Utilização (%)']:.2f}% | Volume {t['Volume (m³)']:.4f} m³") for _,t in ok.head(10).iterrows()]
            if area: optimization_report.extend([('Entre-eixos candidatos (mm)',esp)]+[(f"{int(t['b (mm)'])} x {int(t['h (mm)'])} @ {int(t['Entre-eixos (mm)'])} mm",f"{t['Madeira (m³/m²)']:.5f} m³/m² | {t['Custo madeira (€/m²)']:.2f} €/m²") for _,t in ok.head(10).iterrows()])
            if not travada: st.warning('Estabilidade lateral não avaliada na pesquisa: o momento crítico externo da secção manual não é transferível. Resultados apenas parciais.')
            st.metric('Candidatas dentro dos critérios calculados',f'{len(ok)} / {len(df)}')
            if ok.empty: st.error('Nenhuma candidata satisfaz os critérios calculados.')
            else:
                best=ok.iloc[0]; st.metric('Primeira candidata (mm)',f"{int(best['b (mm)'])} × {int(best['h (mm)'])}")
                if area: st.metric('Entre-eixos da primeira candidata (mm)',f"{best['Entre-eixos (mm)']:.0f}")
                st.caption('Para verificar em detalhe, introduzir estas dimensões nos campos manuais da barra lateral.')
                st.dataframe(ok.style.format({'Volume (m³)':'{:.4f}','Utilização (%)':'{:.2f}','Custo estimado (€)':'{:.2f}','f1 (Hz)':'{:.2f}'}).set_properties(**{'background-color':'#e0edfa','color':'#24578d'}),hide_index=True)
            with st.expander('Todas as candidatas'):
                st.dataframe(df,hide_index=True)
            st.download_button('Exportar pesquisa CSV',df.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'),'pesquisa_seccoes.csv','text/csv')
        except ValueError as e: st.error(str(e))
st.warning('Pesquisa preliminar: não inclui compressão perpendicular, ligações, fogo ou vibrações do pavimento. Propriedades e parâmetros nacionais por confirmar.')

from report import gerar_pdf
st.header('Memória de cálculo — PDF')
projeto=st.text_input('Projeto',help='Designação da obra ou estudo.')
cliente=st.text_input('Cliente',help='Entidade destinatária do estudo.')
engenheiro=st.text_input('Engenheiro',help='Responsável pela revisão técnica; não constitui assinatura.')
elemento=st.text_input('Referência do elemento',help='Identificador da viga ou pavimento.')
secoes=[('Modelo e dados de entrada',[( 'Apoio',apoio),('Vão (m)',L),('Secção (mm)',f'{b} x {h}'),('Material',mat),('E / G (MPa)',f'{E} / {G}'),('Massa volúmica (kg/m³)',rho),('fm,k / fv,k (MPa)',f'{fm} / {fv}'),('G adicional / Q (kN/m)',f'{g} / {q}'),('Peso próprio (kN/m)',f'{pp:.4f}'),('Classe de serviço / duração',f'{sc} / {dur}'),('kmod G / G+Q; kdef',f'{kp} / {km}; {kd}'),('γM / γG / γQ',f'{gm} / {gg} / {gq}'),('ψ1 / ψ2',f'{psi1} / {psi2}'),('kvar',kvar),('Travamento confirmado',str(travada)),('Mcr / βm / βθ externos',f'{mcr} / {beta_m} / {beta_theta}'),('Contraflecha (mm)',w0),('A / I / W (mm² / mm⁴ / mm³)',f"{r['A']:.0f} / {r['I']:.0f} / {r['W']:.0f}")])]
secoes.append(('Origem das ações',[('Modo',modo),('Entre-eixos (m)',entre),('G / Q introduzidos ('+unidade+')',f'{ge} / {qe}'),('G / Q lineares sem peso próprio (kN/m)',f'{g:.4f} / {q:.4f}')]))
secoes.append(('Combinações de ações — parâmetros provisórios',[(n,f'{c:.3f} kN/m') for n,c in combinacoes(pp+g,q,gg,gq,psi1,psi2).items()]))
for nome,a in checks:
    secoes.append((nome,[(k,'Não avaliada' if a[k] is None else f'{100*a[k]:.2f}%') for k in ('flexao','corte','instabilidade')]+[(k,f'{a[k]:.4f}') for k in ('khm','khv','kv','fmd','fvd')]))
secoes.append(('ELS — deformações (9.2.2)',[(label,f'{np.max(np.abs(d[k])):.3f} mm / {L*1000/n:.3f} mm | {100*np.max(np.abs(d[k]))/(L*1000/n):.2f}%') for label,d,k,n in [('Instantânea característica',res['Característica'],'inst',limite),('Final característica líquida',res['Característica'],'net',nfin),('Final frequente líquida',res['Frequente'],'net',nfreq),('Final quase permanente líquida',res['Quase permanente'],'net',nfin)]]))
secoes.append(('Vibração da viga — triagem não regulamentar',[('Massa linear (kg/m)',f'{massa:.3f}'),('Fração variável',psi),('Frequência / referência (Hz)',f"{r['f']:.3f} / {flim}"),('Flexibilidade / referência (mm/kN)',f"{r['flex']:.3f} / {alim}")]))
secoes.append(('Compressão perpendicular — 8.1.6.1',bearing_report or [('Estado','Não avaliada')]))
secoes.append(('Vibrações do pavimento',floor_report or [('Estado','Não calculado ou fora do domínio')]))
secoes.append(('Pesquisa de secções — primeiras 10 candidatas',optimization_report or [('Estado','Não executada ou inválida')]))
secoes.append(('Referências e limitações',[('Flexão / corte','EC5:2025 8.1.8.1 / 8.1.11.1; sigma = M/W; tau = 1,5 V/A; resistência de cálculo = kmod × kh × fm,k / γM; corte: kv × fv,d.'),('Estabilidade','8.2.2.3; depende de travamento ou análise externa.'),('Deformações','9.2.2; wtot = w1 + w2 + w3; wmax = wtot - w0.'),('Pavimento','9.3.2; método simplificado, sem Anexo E.'),('Pendências','Compressão perpendicular, ligações, fogo, parâmetros nacionais, validação independente. Propriedades indicativas a confirmar. Pesquisa não verifica pavimento completo. Não constitui declaração de conformidade.')]))
pdf=gerar_pdf({'Projeto':projeto,'Cliente':cliente,'Engenheiro':engenheiro,'Elemento':elemento},secoes,[(t,r['x'],r[k]) for t,k in [('Momento fletor não majorado (kNm)','Mx'),('Esforço transverso não majorado (kN)','Vx'),('Deformação por flexão não majorada (mm)','wx')]]+[(f'Deformação líquida — {n} (mm)',d['x'],d['net']) for n,d in res.items()])
st.download_button('Descarregar memória de cálculo PDF',pdf,'TimberDesign_memoria.pdf','application/pdf')
