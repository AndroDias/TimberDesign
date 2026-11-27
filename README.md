# TimberDesign V1.0 Beta

Protótipo de pré-dimensionamento. Não validado para decisões de projeto. A publicação não certifica a conformidade com EN 1995-1-1:2025. Consultar AUDITORIA.txt.

## Windows
Na pasta do projeto: `python -m venv .venv`, depois ` .\.venv\Scripts\python.exe -m pip install -r requirements.txt` e ` .\.venv\Scripts\python.exe -m streamlit run app.py`.

## Publicação
Criar repositório privado no GitHub, carregar os ficheiros deste pacote (não carregar .venv, segredos ou normas). No Streamlit Community Cloud, escolher o repositório, branch main e app.py; selecionar Python 3.13 se disponível. Confirmar privacidade e convidar apenas os testadores autorizados. Não introduzir dados confidenciais de projetos nesta fase.

## Testes
`python -m unittest -v test_regressao`.
As dependências têm intervalos de versões, não um ambiente integralmente reproduzível. Testar a instalação e interface no alojamento antes de convidar utilizadores.
