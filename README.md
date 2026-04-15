Este es un proyecto de Inteligencia Artificial que implementa un agente capaz de resolver laberintos utilizando búsqueda online con DFS
(Búsqueda en Profundidad). Lo interesante es que el agente no conoce el mapa de antemano, sino que va descubriendo el laberinto a medida 
que se mueve. Cuando se queda sin opciones, retrocede por donde vino, y cuando encuentra nuevos caminos, continúa explorando.

Al final del proceso, muestra exactamente todas las celdas por las que pasó y cuál fue la ruta final que encontró hasta la salida.

como correrlo: 
Solo necesitas Python 3.8 en adelante. No hay que instalar bibliotecas adicionales ya que utiliza tkinter, que viene incluido con Python
por defecto. Simplemente se debe ejecutar este comando: python laberinto_agente.py
