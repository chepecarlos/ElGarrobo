"""Colores y estilos de la GUI: todo lo visual que comparten las páginas y componentes"""

COLORES_QUASAR = {"primary": "#00786f", "negative": "#dc2626", "positive": "#15803d"}
"Colores de Quasar con texto blanco encima ≥4.5:1 (los de NiceGUI daban 3.1, 2.6 y 2.5); primary es teal-700 como colorBotones"

# Roles de color: usar estos y no colores sueltos. Los que llevan texto blanco deben dar ≥4.5:1
colorOscuro = "teal-900"
"Cabecera, pestañas y botones del formulario"
colorClaro = "teal-300"
"Texto e íconos de acento sobre fondo oscuro"
colorBotones = "teal-700"
"Botones de herramientas (subir, página, intercambiar…): blanco sobre teal-700 ≈ 5.3:1 (teal-500 daba 2.4:1)"
colorTecla = "teal-700"
"Tecla con acción en teclados y botonera, con su nombre en texto blanco"
colorTeclaVacia = "grey-8"
"Tecla sin acción"
colorActivo = "orange-700"
"Herramienta encendida (modo intercambiar): blanco sobre orange-700 ≈ 5.2:1"
colorPeligro = "negative"
"Borrar, descartar, confirmar salir/reiniciar y errores"
colorBorde = "teal-600"
"Bordes decorativos de paneles y filas (sin texto encima)"
colorTeclaApagada = "grey-10"
"Tecla sin acción en modo Usar: casi invisible, no se puede presionar"
colorSeleccion = "teal-4"
"Opción elegida en los interruptores (Usar/Editar, Cuadrícula/Lista), con texto negro"
colorInterruptor = "teal-10"
"Fondo de la opción no elegida del interruptor Usar/Editar sobre la cabecera"

CSS_BOTONERA = """
/* Únicos colores fijos del CSS: el fondo de la carcasa, el foco (teal-300, mismo que colorClaro) y el texto de error */
:root { --color-carcasa: #0b1716; --color-foco: #5eead4; --color-error-texto: #f87171; }
/* primary y negative (ver COLORES_QUASAR) son fondos con texto blanco; como texto sobre el fondo oscuro no llegan a 4.5:1.
   En campos, menús y botones planos se usa el teal claro y un rojo claro para la etiqueta, la opción elegida y los errores */
.q-field, .q-menu, .q-btn--flat { --q-primary: var(--color-foco); }
.q-field { --q-negative: var(--color-error-texto); }
.modo-usar > .q-splitter__separator { display: none; }
.carcasa {
    background: var(--color-carcasa);
    border-radius: 1.75rem;
    padding: 1.5rem;
    box-shadow: 0 18px 40px -12px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.tecla-viva { touch-action: none; user-select: none; -webkit-touch-callout: none; transition: transform 90ms cubic-bezier(0.16, 1, 0.3, 1), filter 90ms cubic-bezier(0.16, 1, 0.3, 1); }
.tecla-viva:active { transform: scale(0.94); filter: brightness(1.35); }
/* Foco con teclado visible en todo lo que se presiona: el tinte de Quasar casi no se ve sobre los botones teal.
   Quasar pone .no-outline { outline: 0 !important } en q-btn y q-toggle (las teclas también son q-btn) dentro de la capa
   quasar_importants; con !important gana la capa declarada antes, por eso esta va en base y no suelta */
@layer base {
    .tecla-viva:focus-visible, .opcion-distribucion:focus-visible, .q-btn:focus-visible, .q-toggle:focus-visible, .q-item:focus-visible { outline: 2px solid var(--color-foco) !important; outline-offset: 3px; }
}
.q-tab:focus-visible { outline: 2px solid var(--color-foco); outline-offset: -2px; }
/* Navegar: la página entra desde el lado hacia donde se fue (adentro/siguiente → derecha, arriba/anterior → izquierda) */
@keyframes navega-entra { from { opacity: 0.3; transform: translateX(16px); } }
@keyframes navega-sale { from { opacity: 0.3; transform: translateX(-16px); } }
@keyframes navega-funde { from { opacity: 0.3; } }
.navega-entra { animation: navega-entra 220ms cubic-bezier(0.16, 1, 0.3, 1); }
.navega-sale { animation: navega-sale 220ms cubic-bezier(0.16, 1, 0.3, 1); }
@media (prefers-reduced-motion: reduce) {
    .tecla-viva { transition: none; }
    .navega-entra, .navega-sale { animation: navega-funde 160ms ease-out; }
}
/* Celular y tablet: el splitter deja el formulario en 20% del ancho, se apila debajo del dispositivo */
@media (max-width: 1023px) {
    .pagina-acciones.q-splitter { flex-direction: column; }
    .pagina-acciones > .q-splitter__panel { width: 100% !important; }
    .pagina-acciones > .q-splitter__before { order: 2; }
    .pagina-acciones > .q-splitter__separator { display: none; }
}
/* Escritorio: las pestañas de dispositivos van en la cabecera, en una grilla con los lados iguales para que
   no se muevan cuando cambia el folder o la última acción; en pantallas angostas bajan a una segunda fila.
   --alto-cabecera lo actualiza un ResizeObserver (paginaAcciones) para que los altos en vh no dependan de las filas */
:root { --alto-cabecera: 48px; }
.cabecera-grilla { display: grid !important; grid-template-columns: minmax(0, 1fr) minmax(0, max-content) minmax(0, 1fr); }
@media (max-width: 1023px) {
    .cabecera-grilla { grid-template-columns: auto minmax(0, 1fr); }
    .cabecera-pestañas { order: 99; grid-column: 1 / -1; }
}
/* Dedo: botones e interruptores llegan a 44px; las teclas no, miden lo que mide la tecla del aparato */
@media (pointer: coarse) {
    .q-btn:not(.tecla-viva), .q-toggle { min-height: 44px; }
    .q-btn--round:not(.tecla-viva) { min-width: 44px; }
}
/* Vista lista: cada fila es su propia grilla, la columna de botones es fija para que todas midan igual; en celular se ocultan Título y Acción */
.fila-acciones { width: 100%; display: grid; grid-template-columns: minmax(6rem, 2fr) minmax(5rem, 1.5fr) minmax(3.5rem, 1fr) minmax(6rem, 1.5fr) 10.25rem; gap: 0.5rem; align-items: center; }
.fila-acciones > * { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fila-acciones > *:last-child { overflow: visible; }
@media (max-width: 639px) {
    .fila-acciones { grid-template-columns: minmax(3rem, 1fr) 2.5rem 10.25rem; gap: 0.25rem; }
    .cabecera-acciones > * { overflow: visible; }
    .fila-acciones > .solo-ancho { display: none; }
}
"""
