# Carpeta donde guardar la documentación
DOCS_DIR = docs

# Paquete o ruta del código a documentar
PACKAGE = src/elGarrobo

install:
	@echo "Instalando Paquete..."
	pipx install . --force

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

extras:
	@echo "Instalando paquetes extras"
	sudo apt install -y python3-pip python3-setuptools python3-tk python3-dev pipx ffmpeg git 
	sudo apt install -y libasound2-dev
	@echo "Instalado Manejador de ventana"
	sudo apt install -y xdotool
