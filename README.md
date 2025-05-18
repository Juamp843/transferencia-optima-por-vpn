hola gracia por revisar nuestro programa, para empezar todos los codigos enencuentran en la carpeta src ahi encontras 4 archivos .py, app_dijsktra, app_kruskal, menu_principal y network.
el pimero contiene la interfaz y los algoritmos necesarios para la implementacion del algoritmo dijsktra. 
el segundo de igualmenera incluye la interfaz y el algoritmo kruskal.
el codigo menu_principal es la plantilla donde se visualizaran los primeros dos codigos, este es el codigo que unifica para una mejor manipulacion de estos.
el archivo network es el script que nos permitira hacer el calculo de latencias con las ip de la red privada a la que estemos conectadas, el codigo no esta invocado en ninguno de los otros
sinembargo parte de su estructura si esta implementada en los 2 primeros codigo, este codigo se subio con la finalidad de analizar su implementacion en estos dos codigos.

app kruskal.
Se utilizó el algoritmo de Kruskal como herramienta para optimizar las conexiones dentro de una
red de dispositivos. Este algoritmo, perteneciente a la teoría de grafos, permite construir el árbol de
expansión mínima (MST, por sus siglas en inglés), es decir, una estructura que conecta todos los
nodos de un grafo con el menor costo total posible, evitando ciclos y conexiones redundantes.
Para su aplicación, primero se identificaron todos los dispositivos en la red mediante sus
direcciones IP. Posteriormente, se midió la latencia entre cada par de dispositivos utilizando
comandos de ping. Estos valores de latencia se utilizaron como pesos en las aristas del grafo.
Una vez recopiladas las latencias, se construyó un grafo completo que incluye todos los nodos
(dispositivos) y todas las posibles conexiones entre ellos. El algoritmo de Kruskal ordenó todas las
aristas en función de su peso (latencia), y seleccionó las conexiones de menor costo una por una,
asegurándose de no formar ciclos, hasta conectar todos los nodos.
El resultado fue un árbol de expansión mínima, una representación óptima de la red donde se
minimiza el uso de recursos y se reduce la latencia total. Este árbol permitió visualizar las rutas más
eficientes entre los dispositivos y sirvió como base para tomar decisiones posteriores, como la
transferencia directa de archivos entre los dispositivos conectados según la estructura optimizada.
Gracias a este enfoque, fue posible identificar no solo la conectividad total, sino también la
eficiencia de dicha conectividad, priorizando la comunicación entre los dispositivos que presentan
menor latencia entre sí.

app  Dijkstra.
Interfaz gráfica
Utilicé CustomTkinter para crear una interfaz moderna y amigable que incluye:
•	Un selector de archivos para elegir qué transferir
•	Menús desplegables para seleccionar servidor origen y destino
•	Opciones para optimizar por latencia, ancho de banda o un balance entre ambos
•	Visualización gráfica de la red como un grafo
•	Panel de información que muestra detalles de la ruta y la transferencia
•	Barra de progreso para monitorear las transferencias en tiempo real
Algoritmo de Dijkstra y cálculo de rutas
Implementé el algoritmo de Dijkstra usando NetworkX para encontrar el camino más eficiente entre los servidores. El sistema:
•	Mide la latencia hacia cada servidor mediante comandos ping
•	Estima el ancho de banda usando speedtest-cli
•	Construye un grafo donde los nodos son servidores y las aristas son conexiones
•	Calcula los pesos de las aristas combinando latencia y ancho de banda
•	Encuentra la ruta óptima según el criterio seleccionado
Visualización de la red
Para la visualización gráfica, utilicé matplotlib y NetworkX para:
•	Mostrar todos los servidores en un diseño circular
•	Representar las conexiones entre servidores
•	Mostrar información de latencia y ancho de banda en cada conexión
•	Resaltar en rojo la ruta óptima cuando se calcula
Requisitos para usar la aplicación
Bibliotecas Python necesarias
pip install customtkinter matplotlib networkx pillow speedtest-cli
Configuración de red
Para que todo funcione correctamente, se necesita:
1.	ZeroTier instalado y configurado en todos los servidores
2.	Una carpeta compartida llamada "ZT_Share" en cada servidor (C:\ZT_Share)
3.	Permisos SMB correctamente configurados
4.	Firewall con el puerto 445 (SMB) abierto entre los nodos
