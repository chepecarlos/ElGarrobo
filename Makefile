# Targets que son acciones y no archivos: se ejecutan siempre aunque exista una carpeta con ese nombre (ej. docs/, capturas/)
.PHONY: install uninstall install-dev docs serve-docs clean-docs test test-cov test-cov-html extras capturas

# Carpeta donde guardar la documentación
DOCS_DIR = docs

# Paquete o ruta del código a documentar
PACKAGE = src/elGarrobo

install:
	@echo "Instalando Paquete..."
	pipx install . --force
	$$(pipx environment --value PIPX_BIN_DIR)/elgarrobo servicio instalar

uninstall:
	@echo "Desinstalando Paquete..."
	-$$(pipx environment --value PIPX_BIN_DIR)/elgarrobo servicio desinstalar
	pipx uninstall elgarrobo

# Instalar en venv editable para pruebas (los cambios en src/ se ven sin reinstalar)
install-dev:
	@echo "Instalando Paquete en venv para pruebas..."
	test -d venv || python3 -m venv venv
	venv/bin/pip install -e ".[dev]"

# Generar documentación
docs:
	@echo "Generando documentación con pdoc..."
	pdoc $(PACKAGE) -o $(DOCS_DIR) --docformat google

# Servir documentación localmente
serve-docs:
	@echo "Sirviendo documentación en http://localhost:1234 ..."
	pdoc $(PACKAGE) -p 1234 --docformat google

# Limpiar carpeta de documentación
clean-docs:
	@echo "Eliminando carpeta de documentación..."
	rm -rf $(DOCS_DIR)

# Ejecutar tests
test:
	@echo "Ejecutando tests..."
	pytest tests/ -v

# Ejecutar tests con cobertura
test-cov:
	@echo "Ejecutando tests con cobertura..."
	pytest tests/ -v --cov=src/elGarrobo --cov-report=term-missing

# Ejecutar tests con reporte HTML
test-cov-html:
	@echo "Ejecutando tests con reporte HTML..."
	pytest tests/ --cov=src/elGarrobo --cov-report=html
	@echo "Reporte generado en htmlcov/index.html"

# Capturas de la GUI en tema oscuro y claro para revisarlas a ojo (Playwright con el Google Chrome del sistema)
capturas:
	@echo "Tomando capturas de la GUI..."
	venv/bin/python tests/visual/capturas.py
	@echo "Capturas en capturas/"

extras:
	@echo "Instalando paquetes extras"
	sudo apt install -y python3-pip python3-setuptools python3-tk python3-dev pipx ffmpeg git 
	sudo apt install -y libasound2-dev
	@echo "Instalado Manejador de ventana"
	@echo "Instalando xdotool para simulación de teclado con caracteres especiales"
	sudo apt install -y xdotool
	@echo "Instalando soporte para el ícono en la barra de estado"
	sudo apt install -y python3-gi gir1.2-ayatanaappindicator3-0.1
