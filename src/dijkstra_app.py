import customtkinter as ctk
import subprocess
import speedtest as st
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import platform
import os
import time
import threading
import io
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class DijkstraApp(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.hosts = ["172.29.150.87", "172.29.5.37", "172.29.130.128", "172.29.127.70", "172.29.42.70", "172.29.155.85"]
        self.host_names = {
            "172.29.150.87": "Server 1",
            "172.29.5.37": "Server 2",
            "172.29.130.128": "Server 3",
            "172.29.127.70": "Server 4",
            "172.29.42.70": "Server 5",
            "172.29.155.85": "Server 6"
            
            
        }
        
        self.latencias = {}
        self.bandwidths = {}
        self.grafo = None
        self.ruta_optima = None
        self.archivos_seleccionados = []
        
        self.create_widgets()
        self.inicializar_grafo()
    
    def create_widgets(self):
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Frame superior
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        top_frame.grid_columnconfigure((0,1,2), weight=1)
        
        # Frame de selección de archivos
        file_frame = ctk.CTkFrame(top_frame)
        file_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkButton(file_frame, text="Seleccionar Archivos", 
                     command=self.seleccionar_archivos).pack(pady=5)
        
        self.files_label = ctk.CTkLabel(file_frame, text="Ningún archivo seleccionado")
        self.files_label.pack(pady=5)
        
        # Frame de origen/destino
        nodes_frame = ctk.CTkFrame(top_frame)
        nodes_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.origen_seleccionado = ctk.StringVar()
        self.destino_seleccionado = ctk.StringVar()
        
        ctk.CTkLabel(nodes_frame, text="Origen:").grid(row=0, column=0, padx=5, pady=5)
        origen_combo = ctk.CTkComboBox(nodes_frame, variable=self.origen_seleccionado)
        origen_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        origen_combo.configure(values=[f"{self.host_names.get(host, host)} ({host})" for host in self.hosts])
        
        ctk.CTkLabel(nodes_frame, text="Destino:").grid(row=1, column=0, padx=5, pady=5)
        destino_combo = ctk.CTkComboBox(nodes_frame, variable=self.destino_seleccionado)
        destino_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        destino_combo.configure(values=[f"{self.host_names.get(host, host)} ({host})" for host in self.hosts])
        
        # Frame de opciones
        opt_frame = ctk.CTkFrame(top_frame)
        opt_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.optimize_for = ctk.StringVar(value="balanced")
        
        ctk.CTkLabel(opt_frame, text="Optimización:").pack(pady=(5,0))
        ctk.CTkRadioButton(opt_frame, text="Latencia", variable=self.optimize_for, 
                          value="latency").pack(anchor="w", padx=5, pady=2)
        ctk.CTkRadioButton(opt_frame, text="Ancho de Banda", variable=self.optimize_for, 
                          value="bandwidth").pack(anchor="w", padx=5, pady=2)
        ctk.CTkRadioButton(opt_frame, text="Balanceado", variable=self.optimize_for, 
                          value="balanced").pack(anchor="w", padx=5, pady=2)
        
        # Frame principal para el gráfico
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Frame para el gráfico
        graph_frame = ctk.CTkFrame(main_frame)
        graph_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        graph_frame.grid_columnconfigure(0, weight=1)
        graph_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas para el grafo
        self.canvas = ctk.CTkCanvas(graph_frame, bg="#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Frame inferior
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=2, column=0, padx=10, pady=(0,10), sticky="nsew")
        
        # Información de transferencia
        info_frame = ctk.CTkFrame(bottom_frame)
        info_frame.pack(fill="x", pady=5)
        
        self.info_text = ctk.CTkTextbox(info_frame, height=100)
        self.info_text.pack(fill="x", pady=5)
        self.info_text.configure(state="disabled")
        
        # Barra de progreso
        self.progress = ctk.CTkProgressBar(bottom_frame, orientation="horizontal")
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        
        # Botones
        button_frame = ctk.CTkFrame(bottom_frame)
        button_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(button_frame, text="Calcular Ruta Óptima", 
                     command=self.calcular_ruta).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="Iniciar Transferencia", 
                     command=self.iniciar_transferencia).pack(side="left", padx=5)
    
    def seleccionar_archivos(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos para transferir",
            filetypes=(("Todos los archivos", "*.*"),)
        )
        
        if files:
            self.archivos_seleccionados = files
            if len(files) == 1:
                self.files_label.configure(text=f"1 archivo: {os.path.basename(files[0])}")
            else:
                self.files_label.configure(text=f"{len(files)} archivos seleccionados")
        else:
            self.archivos_seleccionados = []
            self.files_label.configure(text="Ningún archivo seleccionado")
    
    def medir_latencia(self, host):
        """Mide la latencia a un host mediante comandos ping."""
        so = platform.system().lower()
        if so == "windows":
            comando = ["ping", "-n", "4", host]
        else:
            comando = ["ping", "-c", "4", host]

        try:
            resultado = subprocess.run(comando, capture_output=True, text=True, timeout=10)
            salida = resultado.stdout

            # Procesar salida según sistema operativo
            latencias_lista = []
            if so == "windows":
                lineas = [line for line in salida.split("\n") if "Tiempo=" in line or "tiempo=" in line]
                for linea in lineas:
                    partes = linea.split("Tiempo=" if "Tiempo=" in linea else "tiempo=")
                    if len(partes) > 1:
                        tiempo = partes[1].split("ms")[0].strip()
                        latencias_lista.append(float(tiempo))
            else:
                lineas = [line for line in salida.split("\n") if "time=" in line]
                for linea in lineas:
                    partes = linea.split("time=")
                    if len(partes) > 1:
                        tiempo = partes[1].split(" ")[0]
                        latencias_lista.append(float(tiempo))

            if latencias_lista:
                promedio = sum(latencias_lista) / len(latencias_lista)
                self.latencias[host] = promedio
                return promedio
            else:
                return None

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Error midiendo latencia en {host}: {e}")
            return None

    def medir_ancho_de_banda(self):
        """Mide el ancho de banda de subida y bajada usando speedtest-cli."""
        try:
            speed = st.Speedtest()
            speed.get_best_server()
            download_speed = speed.download() / 1e6  # Mbps
            upload_speed = speed.upload() / 1e6  # Mbps
            return download_speed, upload_speed
        except Exception as e:
            print(f"Error midiendo ancho de banda: {e}")
            return None, None

    def estimar_ancho_de_banda_entre_hosts(self):
        """Estima el ancho de banda entre todos los pares de hosts."""
        download, upload = self.medir_ancho_de_banda()
        
        # Valores por defecto si no se puede medir
        if download is None:
            download = 100  # 100 Mbps por defecto
        if upload is None:
            upload = 50     # 50 Mbps por defecto
        
        # Crear matriz de ancho de banda entre hosts
        for i, host1 in enumerate(self.hosts):
            for j, host2 in enumerate(self.hosts):
                if i != j:  # No medir ancho de banda de un host a sí mismo
                    factor = 0.8 + (((i+1)*(j+1)) % 5) / 10.0  # Valores entre 0.8 y 1.2
                    bandwidth = min(download, upload) * factor
                    key = f"{host1}-{host2}"
                    self.bandwidths[key] = bandwidth

    def construir_grafo(self):
        """Construye el grafo de red con las mediciones actuales."""
        # Medir latencias
        for host in self.hosts:
            self.medir_latencia(host)
        
        # Medir/estimar anchos de banda
        self.estimar_ancho_de_banda_entre_hosts()
        
        # Crear grafo con NetworkX
        G = nx.Graph()
        
        # Añadir nodos
        for host in self.hosts:
            G.add_node(host, latency=self.latencias.get(host, float('inf')))
        
        # Añadir aristas con pesos
        for i, host1 in enumerate(self.hosts):
            for j, host2 in enumerate(self.hosts):
                if i < j:  # Para evitar duplicados
                    latencia_promedio = (self.latencias.get(host1, 0) + self.latencias.get(host2, 0)) / 2
                    ancho_banda = self.bandwidths.get(f"{host1}-{host2}", 0) or self.bandwidths.get(f"{host2}-{host1}", 0)
                    
                    if ancho_banda > 0:
                        peso = latencia_promedio / ancho_banda * 1000  # Factor de escala
                    else:
                        peso = float('inf')
                    
                    G.add_edge(host1, host2, weight=peso, latency=latencia_promedio, bandwidth=ancho_banda)
        
        return G

    def dijkstra(self, grafo, origen, destino, optimize_for='latency'):
        """Implementa el algoritmo de Dijkstra para encontrar la ruta óptima."""
        if optimize_for == 'latency':
            ruta = nx.shortest_path(grafo, origen, destino, weight='weight')
        elif optimize_for == 'bandwidth':
            G_temp = nx.Graph()
            for u, v, data in grafo.edges(data=True):
                G_temp.add_edge(u, v, weight=1.0/data['bandwidth'] if data['bandwidth'] > 0 else float('inf'))
            ruta = nx.shortest_path(G_temp, origen, destino, weight='weight')
        else:
            ruta = nx.shortest_path(grafo, origen, destino, weight='weight')
        return ruta

    def generar_imagen_grafo(self, grafo, ruta_optima=None):
        """Genera una imagen del grafo de red con la ruta óptima resaltada."""
        try:
            G = nx.Graph()
            
            # Añadir nodos
            for i, host in enumerate(self.hosts):
                nombre = self.host_names.get(host, host)
                G.add_node(host, label=f"{nombre}\n({host})")
            
            # Añadir aristas
            for i, host1 in enumerate(self.hosts):
                for j, host2 in enumerate(self.hosts):
                    if i < j:  # Para evitar duplicados
                        key1 = f"{host1}-{host2}"
                        key2 = f"{host2}-{host1}"
                        latencia = (self.latencias.get(host1, 0) + self.latencias.get(host2, 0)) / 2
                        ancho_banda = self.bandwidths.get(key1, 0) or self.bandwidths.get(key2, 0)
                        
                        es_ruta_optima = False
                        if ruta_optima and len(ruta_optima) > 1:
                            for k in range(len(ruta_optima) - 1):
                                if (ruta_optima[k] == host1 and ruta_optima[k+1] == host2) or \
                                   (ruta_optima[k] == host2 and ruta_optima[k+1] == host1):
                                    es_ruta_optima = True
                                    break
                        
                        G.add_edge(host1, host2, 
                                  weight=1 + (latencia / 50),
                                  color='red' if es_ruta_optima else 'gray',
                                  label=f"{latencia:.1f}ms\n{ancho_banda:.1f}Mbps")
            
            # Crear figura
            fig = plt.figure(figsize=(7, 7), dpi=100)
            ax = fig.add_subplot(111)
            pos = nx.circular_layout(G)
            
            # Dibujar componentes del grafo
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color='skyblue', node_size=1000)
            nx.draw_networkx_labels(G, pos, ax=ax, 
                                   labels={node: data['label'] for node, data in G.nodes(data=True)},
                                   font_size=8)
            
            for u, v, data in G.edges(data=True):
                nx.draw_networkx_edges(G, pos, ax=ax, edgelist=[(u, v)], 
                                      width=data['weight'], 
                                      edge_color=data['color'])
            
            edge_labels = {(u, v): data['label'] for u, v, data in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels, font_size=7)
            
            ax.set_title('Grafo de Red y Ruta Óptima')
            ax.axis('off')
            fig.tight_layout()
            
            # Guardar a buffer
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            plt.close(fig)
            
            return buffer
            
        except Exception as e:
            print(f"Error generando visualización: {str(e)}")
            fig = plt.figure(figsize=(7, 7), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error al generar visualización:\n{str(e)}", 
                   ha='center', va='center', fontsize=12)
            ax.axis('off')
            
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            plt.close(fig)
            
            return buffer

    def simular_transferencia(self, origen, destino, ruta, tamaño_archivo, progress_callback=None):
        """Simula la transferencia de un archivo a través de una ruta específica."""
        tiempo_total = 0
        
        # Calcular tiempo total estimado
        for i in range(len(ruta) - 1):
            nodo_actual = ruta[i]
            nodo_siguiente = ruta[i + 1]
            
            key1 = f"{nodo_actual}-{nodo_siguiente}"
            key2 = f"{nodo_siguiente}-{nodo_actual}"
            ancho_banda = self.bandwidths.get(key1, 0) or self.bandwidths.get(key2, 0)
            
            if ancho_banda <= 0:
                ancho_banda = 10  # Mbps por defecto
            
            tiempo_hop = (tamaño_archivo * 8) / ancho_banda
            tiempo_total += tiempo_hop
        
        # Simular transferencia con actualizaciones de progreso
        tiempo_inicio = time.time()
        tiempo_transcurrido = 0
        
        while tiempo_transcurrido < tiempo_total:
            progreso = min(100, (tiempo_transcurrido / tiempo_total) * 100)
            if progress_callback:
                progress_callback(progreso)
            
            time.sleep(0.1)
            tiempo_transcurrido = time.time() - tiempo_inicio
            
            if tiempo_transcurrido >= tiempo_total:
                if progress_callback:
                    progress_callback(100)
                break
        
        return tiempo_total

    def inicializar_grafo(self):
        """Inicializa el grafo con las mediciones actuales."""
        try:
            self.grafo = self.construir_grafo()
            self.actualizar_visualizacion()
        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar el grafo: {str(e)}")

    def extraer_ip(self, texto):
        """Extrae la IP de un texto con formato 'Nombre (IP)'."""
        if "(" in texto and ")" in texto:
            return texto.split("(")[1].split(")")[0]
        return texto

    def calcular_ruta(self):
        """Calcula la ruta óptima entre origen y destino."""
        if not self.grafo:
            messagebox.showerror("Error", "El grafo no está inicializado")
            return
        
        origen_texto = self.origen_seleccionado.get()
        destino_texto = self.destino_seleccionado.get()
        
        if not origen_texto or not destino_texto:
            messagebox.showerror("Error", "Debe seleccionar un origen y un destino")
            return
        
        origen_ip = self.extraer_ip(origen_texto)
        destino_ip = self.extraer_ip(destino_texto)
        
        if origen_ip == destino_ip:
            messagebox.showerror("Error", "El origen y el destino deben ser diferentes")
            return
        
        try:
            optimize_for = self.optimize_for.get()
            self.ruta_optima = self.dijkstra(self.grafo, origen_ip, destino_ip, optimize_for)
            self.actualizar_visualizacion()
            self.mostrar_info_ruta()
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular la ruta: {str(e)}")

    def actualizar_visualizacion(self):
        """Actualiza la visualización del grafo en el canvas."""
        try:
            buffer = self.generar_imagen_grafo(self.grafo, self.ruta_optima)
            img = Image.open(buffer)
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
            
            self.graph_image = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.graph_image, anchor="nw")
        except Exception as e:
            print(f"Error generando visualización: {str(e)}")
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width()/2, 
                self.canvas.winfo_height()/2,
                text=f"No se pudo generar la visualización.\nVerifique las dependencias.",
                fill="red" if ctk.get_appearance_mode() == "Dark" else "black"
            )

    def mostrar_info_ruta(self):
        """Muestra información detallada sobre la ruta calculada."""
        if not self.ruta_optima:
            return
        
        latencia_total = 0
        ancho_banda_min = float('inf')
        
        for i in range(len(self.ruta_optima) - 1):
            nodo1 = self.ruta_optima[i]
            nodo2 = self.ruta_optima[i + 1]
            
            if (nodo1, nodo2) in self.grafo.edges:
                latencia = self.grafo[nodo1][nodo2].get('latency', 0)
                ancho_banda = self.grafo[nodo1][nodo2].get('bandwidth', 0)
                
                latencia_total += latencia
                if ancho_banda < ancho_banda_min:
                    ancho_banda_min = ancho_banda
        
        if ancho_banda_min == float('inf'):
            ancho_banda_min = 0
        
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        
        ruta_str = " -> ".join([self.host_names.get(host, host) for host in self.ruta_optima])
        self.info_text.insert("end", f"Ruta: {ruta_str}\n")
        self.info_text.insert("end", f"Latencia total: {latencia_total:.2f} ms\n")
        self.info_text.insert("end", f"Ancho de banda mínimo: {ancho_banda_min:.2f} Mbps\n")
        
        if self.archivos_seleccionados:
            tamaño_total = sum(os.path.getsize(f) for f in self.archivos_seleccionados) / (1024 * 1024)
            tiempo_estimado = (tamaño_total * 8) / ancho_banda_min if ancho_banda_min > 0 else 0
            self.info_text.insert("end", f"Tiempo estimado: {tiempo_estimado:.2f} segundos para {tamaño_total:.2f} MB\n")
        
        self.info_text.configure(state="disabled")

    def actualizar_progreso(self, valor):
        """Actualiza la barra de progreso."""
        self.progress.set(valor / 100)

    def iniciar_transferencia(self):
        """Inicia el proceso de transferencia de archivos."""
        if not self.archivos_seleccionados:
            messagebox.showerror("Error", "No hay archivos seleccionados")
            return
        
        if not self.ruta_optima:
            messagebox.showerror("Error", "No se ha calculado una ruta óptima")
            return
        
        tamaño_total = sum(os.path.getsize(f) for f in self.archivos_seleccionados) / (1024 * 1024)
        
        threading.Thread(
            target=self.realizar_transferencia,
            args=(self.ruta_optima[0], self.ruta_optima[-1], self.ruta_optima, tamaño_total),
            daemon=True
        ).start()

    def realizar_transferencia(self, origen, destino, ruta, tamaño_archivo):
        """Realiza la transferencia de archivos en un hilo separado."""
        try:
            messagebox.showinfo("Transferencia", "Iniciando transferencia de archivos...")
            
            tiempo_total = self.simular_transferencia(
                origen, 
                destino, 
                ruta, 
                tamaño_archivo,
                progress_callback=lambda p: self.after(0, lambda: self.actualizar_progreso(p))
            )
            
            messagebox.showinfo("Transferencia", f"Transferencia completada en {tiempo_total:.2f} segundos")
            self.after(0, lambda: self.actualizar_progreso(100))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en la transferencia: {str(e)}")
        finally:
            self.after(2000, lambda: self.actualizar_progreso(0))