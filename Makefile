all: install run

# Testa se o venv já foi criado para criar
venv:
	@test -d venv || python3 -m venv venv

# Requer um venv para executar, testa se tem todas as dependências e instala as faltantes
install: venv
	venv/bin/pip install -r requirements.txt

# Roda o projeto dentro do venv
run: venv
	. venv/bin/activate && streamlit run view.py

cli:
	venv/bin/python dashboard_realtime.py
# Limpa o projeto
clean:
	rm -rf venv
