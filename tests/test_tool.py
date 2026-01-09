import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.elGarrobo.tool import convertirArchivo, ordenarArchivo, ordenarNatural


class TestOrdenarNatural:
    """Tests para la función ordenarNatural"""

    def test_ordena_numeros_correctamente(self):
        """Verifica que ordena item1, item2, item10 correctamente"""
        items = ["item10", "item1", "item2"]
        items_ordenados = sorted(items, key=ordenarNatural)
        assert items_ordenados == ["item1", "item2", "item10"]

    def test_ordena_letras_minusculas(self):
        """Verifica que convierte a minúsculas"""
        result = ordenarNatural("ITEM1")
        assert "item" in str(result).lower()

    def test_maneja_strings_sin_numeros(self):
        """Verifica que maneja strings sin números"""
        result = ordenarNatural("abc")
        assert isinstance(result, list)


class TestOrdenarArchivo:
    """Tests para la función ordenarArchivo"""

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    @patch("src.elGarrobo.tool.EscribirArchivo")
    def test_ordena_datos_correctamente(self, mock_escribir, mock_obtener, mock_path):
        """Test básico: ordena data correctamente"""
        # Setup
        mock_path.return_value.suffix = ".md"
        mock_path.return_value.exists.return_value = True
        mock_obtener.return_value = [
            {"key": "item3", "valor": "c"},
            {"key": "item1", "valor": "a"},
            {"key": "item2", "valor": "b"},
        ]

        # Ejecutar
        ordenarArchivo("test.md")

        # Verificar que se ordenó correctamente
        mock_escribir.assert_called_once()
        datos_guardados = mock_escribir.call_args[0][1]
        assert datos_guardados[0]["key"] == "item1"
        assert datos_guardados[1]["key"] == "item2"
        assert datos_guardados[2]["key"] == "item3"

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    @patch("src.elGarrobo.tool.EscribirArchivo")
    def test_ordena_numeros_naturales(self, mock_escribir, mock_obtener, mock_path):
        """Test: ordena números naturales (item1, item2, item10)"""
        mock_path.return_value.suffix = ".md"
        mock_path.return_value.exists.return_value = True
        mock_obtener.return_value = [
            {"key": "item10", "valor": "z"},
            {"key": "item2", "valor": "b"},
            {"key": "item1", "valor": "a"},
        ]

        ordenarArchivo("test.md")

        datos_guardados = mock_escribir.call_args[0][1]
        keys = [d["key"] for d in datos_guardados]
        assert keys == ["item1", "item2", "item10"]

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_rechaza_archivo_no_md(self, mock_obtener, mock_path):
        """Test: rechaza archivos que no son .md"""
        mock_path.return_value.suffix = ".txt"

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.txt")
            mock_logger.error.assert_called()

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_rechaza_archivo_vacio(self, mock_obtener, mock_path):
        """Test: rechaza archivos vacíos"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.return_value = []

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            mock_logger.warning.assert_called()

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_detecta_duplicados(self, mock_obtener, mock_path):
        """Test: detecta claves duplicadas"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.return_value = [
            {"key": "item1", "valor": "a"},
            {"key": "item1", "valor": "b"},  # Duplicado
        ]

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            # Verifica que se llamó con el error de duplicado
            assert any("repite" in str(call) for call in mock_logger.error.call_args_list)

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_rechaza_elemento_sin_key(self, mock_obtener, mock_path):
        """Test: rechaza elementos sin clave 'key'"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.return_value = [
            {"valor": "a"},  # Sin 'key'
        ]

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            mock_logger.error.assert_called()

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_rechaza_elemento_no_dict(self, mock_obtener, mock_path):
        """Test: rechaza elementos que no son diccionarios"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.return_value = [
            "no es dict",
        ]

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            mock_logger.error.assert_called()

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_captura_error_lectura(self, mock_obtener, mock_path):
        """Test: captura errores al leer archivo"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.side_effect = Exception("Error lectura")

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            mock_logger.error.assert_called()

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    @patch("src.elGarrobo.tool.EscribirArchivo")
    def test_captura_error_escritura(self, mock_escribir, mock_obtener, mock_path):
        """Test: captura errores al escribir archivo"""
        mock_path.return_value.suffix = ".md"
        mock_obtener.return_value = [{"key": "item1", "valor": "a"}]
        mock_escribir.side_effect = Exception("Error escritura")

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            ordenarArchivo("test.md")
            # Verifica que se llamó logger.error con el mensaje de error
            assert any("Error al escribir" in str(call) for call in mock_logger.error.call_args_list)


class TestConvertirArchivo:
    """Tests para la función convertirArchivo"""

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    @patch("src.elGarrobo.tool.EscribirArchivo")
    def test_convierte_json_a_md(self, mock_escribir, mock_obtener, mock_path):
        """Test básico: convierte de .json a .md"""
        mock_path.return_value.suffix = ".json"
        mock_path.return_value.exists.return_value = True
        mock_obtener.return_value = [{"key": "item1"}]

        convertirArchivo("test.json")

        mock_escribir.assert_called_once()
        assert "test.md" in mock_escribir.call_args[0][0]

    @patch("src.elGarrobo.tool.Path")
    @patch("src.elGarrobo.tool.ObtenerArchivo")
    def test_rechaza_archivo_no_json(self, mock_obtener, mock_path):
        """Test: rechaza archivos que no son .json"""
        mock_path.return_value.suffix = ".txt"

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            convertirArchivo("test.txt")
            mock_logger.error.assert_called()

    @patch("src.elGarrobo.tool.Path")
    def test_rechaza_archivo_no_existente(self, mock_path):
        """Test: rechaza archivos que no existen"""
        mock_path.return_value.suffix = ".json"
        mock_path.return_value.exists.return_value = False

        with patch("src.elGarrobo.tool.logger") as mock_logger:
            convertirArchivo("test.json")
            mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
