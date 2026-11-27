import unittest, math
from beam import calcular_viga
from eurocode5 import compressao_apoio, resistencia, coeficientes
from serviceability import deformacoes
class TestMotor(unittest.TestCase):
    def test_apoios(self):
        for apoio,M,V,c in [('Simplesmente apoiada',6.25,5,5/384),('Bi-encastrada',25/6,5,1/384),('Consola',25,10,1/8)]:
            with self.subTest(apoio=apoio):
                r=calcular_viga(5,100,240,11500,2,apoio,50)
                self.assertAlmostEqual(r['M'],M); self.assertAlmostEqual(r['V'],V)
                self.assertAlmostEqual(r['delta'],c*2*5000**4/(11500*115200000))
    def test_fluencia(self):
        d=deformacoes(5,100,240,11500,650,1,1,'Simplesmente apoiada',50,.6,.5,.3,0)['Característica']
        self.assertAlmostEqual(max(d['total'])/max(d['inst']),1.39)
    def test_apoio(self):
        self.assertAlmostEqual(compressao_apoio(10,100,100,2.5,.8,1.25)['util'],.625)
    def test_coeficientes(self):
        self.assertEqual(coeficientes('GL24h',1,'Média'),(.8,.6,1.25))
    def test_esbelteza(self):
        r=resistencia('GL24h',800,24,3.5,.8,1.25,1,5,.5,1000000,mcr=24,beta_m=.1,beta_theta=.1)
        self.assertAlmostEqual(r['lam'],1.)
if __name__=='__main__': unittest.main()

class TestAfastamento(unittest.TestCase):
    def test_conversao(self):
        from cargas import lineares
        self.assertEqual(lineares(1.5,2), (1.5,2))
        g,q=lineares(1.5,2,.6)
        self.assertAlmostEqual(g,.9); self.assertAlmostEqual(q,1.2)
        with self.assertRaises(ValueError): lineares(1,2,0)
    def test_pesquisa(self):
        from optimization import pesquisar
        rows=pesquisar([100],[240],L=5,E=11500,G=650,rho=420,g=1,q=1,apoio='Simplesmente apoiada',psi=.3,mat='GL24h',fm=24,fv=3.5,kp=.6,km=.8,gm=1.25,kvar=1,gg=1.35,gq=1.5,kd=.6,psi1=.5,psi2=.3,w0=0,limite=300,nfin=250,nfreq=300,travada=True,flim=8,alim=1.5,espacamentos=[.05,.4,.6],g_area=1.5,q_area=2,preco=500)
        self.assertEqual(len(rows),2)
        self.assertAlmostEqual(rows[1]['Madeira (m³/m²)'],.04)
        self.assertAlmostEqual(rows[1]['Custo madeira (€/m²)'],20)
        self.assertGreater(rows[1]['Utilização (%)'],rows[0]['Utilização (%)'])
