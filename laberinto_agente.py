import tkinter as tk
import random

FILAS = 13
COLS  = 19
TAM   = 36

DIRS = [(-1, 0, 'N'), (1, 0, 'S'), (0, 1, 'E'), (0, -1, 'W')]
OPP  = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

COLOR_FONDO    = '#1C1C1A'
COLOR_PARED    = '#5F5E5A'
COLOR_VACIO    = '#2C2C2A'
COLOR_VISITADO = '#1a3a30'
COLOR_RUTA     = '#0F6E56'
COLOR_AGENTE   = '#1D9E75'
COLOR_META     = '#993C1D'
COLOR_SOLUCION = '#FFFFFF'
COLOR_LINEA    = '#FAC775'
COLOR_INICIO   = '#3C3489'
COLOR_BOTON    = '#2C2C2A'
COLOR_BTN_HOV  = '#3a3a38'
COLOR_TEXTO    = '#D3D1C7'


def generar_laberinto(filas, cols):
    paredes = [[{'N': True, 'S': True, 'E': True, 'W': True} for _ in range(cols)] for _ in range(filas)]
    visitado = [[False] * cols for _ in range(filas)]
    pila = [(0, 0)]
    visitado[0][0] = True

    while pila:
        r, c = pila[-1]
        vecinos = [
            (r + dr, c + dc, d)
            for dr, dc, d in DIRS
            if 0 <= r + dr < filas and 0 <= c + dc < cols and not visitado[r + dr][c + dc]
        ]
        if not vecinos:
            pila.pop()
            continue
        nr, nc, d = random.choice(vecinos)
        paredes[r][c][d] = False
        paredes[nr][nc][OPP[d]] = False
        visitado[nr][nc] = True
        pila.append((nr, nc))

    return paredes


class AgenteOnline:
    def __init__(self, filas, cols):
        self.r = 0
        self.c = 0
        self.filas = filas
        self.cols  = cols
        self.visitados  = {(0, 0)}
        self.camino     = []
        self.camino_set = set()
        self.pasos      = 0
        self.terminado  = False
        self.encontrado = False
        self.solucion   = None

    def tick(self, paredes):
        if self.terminado:
            return

        r, c = self.r, self.c

        if r == self.filas - 1 and c == self.cols - 1:
            self.terminado  = True
            self.encontrado = True
            self.solucion   = list(self.camino) + [(r, c)]
            return

        opciones = [
            (r + dr, c + dc)
            for dr, dc, d in DIRS
            if not paredes[r][c][d] and (r + dr, c + dc) not in self.visitados
        ]

        if opciones:
            self.camino.append((r, c))
            self.camino_set.add((r, c))
            nr, nc = opciones[0]
            self.visitados.add((nr, nc))
            self.r, self.c = nr, nc
        elif self.camino:
            pr, pc = self.camino.pop()
            self.camino_set.discard((pr, pc))
            self.r, self.c = pr, pc
        else:
            self.terminado = True

        self.pasos += 1


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Agente — Búsqueda Online en Laberinto')
        self.root.configure(bg=COLOR_FONDO)
        self.root.resizable(False, False)

        self.paredes   = None
        self.agente    = None
        self.corriendo = False
        self._job      = None

        self._build_ui()
        self._nuevo()

    def _build_ui(self):
        panel_top = tk.Frame(self.root, bg=COLOR_FONDO, pady=10, padx=12)
        panel_top.pack(fill='x')

        self.btn_nuevo = self._boton(panel_top, 'Nuevo laberinto', self._nuevo)
        self.btn_nuevo.pack(side='left', padx=(0, 6))

        self.btn_start = self._boton(panel_top, 'Iniciar agente', self._arrancar)
        self.btn_start.pack(side='left', padx=(0, 6))

        self.btn_pausa = self._boton(panel_top, 'Pausar', self._toggle_pausa)
        self.btn_pausa.pack(side='left')
        self.btn_pausa.config(state='disabled')

        frm_vel = tk.Frame(panel_top, bg=COLOR_FONDO)
        frm_vel.pack(side='right')
        tk.Label(frm_vel, text='Velocidad', bg=COLOR_FONDO, fg=COLOR_TEXTO,
                 font=('Helvetica', 11)).pack(side='left', padx=(0, 6))
        self.vel = tk.IntVar(value=7)
        tk.Scale(frm_vel, from_=1, to=20, orient='horizontal', variable=self.vel,
                 bg=COLOR_FONDO, fg=COLOR_TEXTO, highlightthickness=0,
                 troughcolor=COLOR_BOTON, activebackground=COLOR_AGENTE,
                 length=100, showvalue=False).pack(side='left')

        contenedor = tk.Frame(self.root, bg=COLOR_FONDO, padx=12, pady=4)
        contenedor.pack()

        self.canvas = tk.Canvas(contenedor, width=COLS * TAM, height=FILAS * TAM,
                                bg=COLOR_VACIO, highlightthickness=1,
                                highlightbackground=COLOR_PARED)
        self.canvas.pack(side='left')

        panel_info = tk.Frame(contenedor, bg=COLOR_FONDO, padx=14)
        panel_info.pack(side='left', fill='y')

        self.lbl_estado  = self._metrica(panel_info, 'Estado', 'Listo', grande=False)
        self.lbl_visitas = self._metrica(panel_info, 'Celdas exploradas', '1')
        self.lbl_pasos   = self._metrica(panel_info, 'Movimientos', '0')
        self.lbl_sol     = self._metrica(panel_info, 'Longitud solución', '—')

        leyenda = tk.Frame(panel_info, bg=COLOR_BOTON, pady=10, padx=12)
        leyenda.pack(fill='x', pady=(8, 0))
        tk.Label(leyenda, text='Leyenda', bg=COLOR_BOTON, fg=COLOR_TEXTO,
                 font=('Helvetica', 11, 'bold')).pack(anchor='w', pady=(0, 6))

        items = [
            (COLOR_AGENTE,   '●', 'Agente'),
            (COLOR_VISITADO, '■', 'Visitado'),
            (COLOR_RUTA,     '■', 'Ruta activa (DFS)'),
            (COLOR_META,     '■', 'Meta'),
            (COLOR_SOLUCION, '■', 'Solución (celdas)'),
            (COLOR_LINEA,    '—', 'Línea de camino'),
        ]
        for col, icono, etiq in items:
            fila = tk.Frame(leyenda, bg=COLOR_BOTON)
            fila.pack(anchor='w', pady=2)
            tk.Label(fila, text=icono, bg=COLOR_BOTON, fg=col,
                     font=('Helvetica', 13)).pack(side='left', padx=(0, 6))
            tk.Label(fila, text=etiq, bg=COLOR_BOTON, fg=COLOR_TEXTO,
                     font=('Helvetica', 10)).pack(side='left')

    def _boton(self, parent, texto, cmd):
        b = tk.Button(parent, text=texto, command=cmd,
                      bg=COLOR_BOTON, fg=COLOR_TEXTO, relief='flat',
                      font=('Helvetica', 11), padx=12, pady=5, cursor='hand2',
                      activebackground=COLOR_BTN_HOV, activeforeground=COLOR_TEXTO, bd=0)
        b.bind('<Enter>', lambda e: b.config(bg=COLOR_BTN_HOV))
        b.bind('<Leave>', lambda e: b.config(bg=COLOR_BOTON))
        return b

    def _metrica(self, parent, label, valor, grande=True):
        frm = tk.Frame(parent, bg=COLOR_BOTON, pady=8, padx=12)
        frm.pack(fill='x', pady=(0, 8))
        tk.Label(frm, text=label, bg=COLOR_BOTON, fg='#888780',
                 font=('Helvetica', 10)).pack(anchor='w')
        lbl = tk.Label(frm, text=valor, bg=COLOR_BOTON, fg=COLOR_TEXTO,
                       font=('Helvetica', 20 if grande else 13,
                             'bold' if grande else 'normal'))
        lbl.pack(anchor='w')
        return lbl

    def _nuevo(self):
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self.corriendo = False
        self.paredes   = generar_laberinto(FILAS, COLS)
        self.agente    = AgenteOnline(FILAS, COLS)
        self.btn_start.config(text='Iniciar agente', state='normal')
        self.btn_pausa.config(state='disabled', text='Pausar')
        self._actualizar_ui()
        self._dibujar()

    def _arrancar(self):
        if self.agente.terminado:
            self._nuevo()
            return
        if self.corriendo:
            return
        self.corriendo = True
        self.btn_pausa.config(state='normal')
        self._loop()

    def _toggle_pausa(self):
        self.corriendo = not self.corriendo
        self.btn_pausa.config(text='Pausar' if self.corriendo else 'Continuar')
        if self.corriendo:
            self._loop()

    def _loop(self):
        if not self.corriendo:
            return
        v = self.vel.get()
        n = max(1, v - 10) if v > 12 else 1
        for _ in range(n):
            if not self.agente.terminado:
                self.agente.tick(self.paredes)
        self._dibujar()
        self._actualizar_ui()
        if self.agente.terminado:
            self.corriendo = False
            self.btn_pausa.config(state='disabled')
            return
        self._job = self.root.after(max(5, 220 - v * 15), self._loop)

    def _dibujar(self):
        self.canvas.delete('all')
        ag      = self.agente
        sol_set = set(map(tuple, ag.solucion)) if ag.solucion else set()

        for r in range(FILAS):
            for c in range(COLS):
                x, y  = c * TAM, r * TAM
                clave = (r, c)

                if ag.solucion:
                    fill = COLOR_SOLUCION if clave in sol_set else COLOR_VISITADO
                elif r == 0 and c == 0:
                    fill = COLOR_INICIO
                elif r == FILAS - 1 and c == COLS - 1:
                    fill = COLOR_META
                elif clave in ag.camino_set:
                    fill = COLOR_RUTA
                elif clave in ag.visitados:
                    fill = COLOR_VISITADO
                else:
                    fill = COLOR_VACIO

                self.canvas.create_rectangle(x + 1, y + 1, x + TAM - 1, y + TAM - 1,
                                             fill=fill, outline='')

                w  = self.paredes[r][c]
                kw = dict(fill=COLOR_PARED, width=2)
                if w['N']: self.canvas.create_line(x,       y,       x + TAM, y,       **kw)
                if w['S']: self.canvas.create_line(x,       y + TAM, x + TAM, y + TAM, **kw)
                if w['W']: self.canvas.create_line(x,       y,       x,       y + TAM, **kw)
                if w['E']: self.canvas.create_line(x + TAM, y,       x + TAM, y + TAM, **kw)

        if ag.solucion and len(ag.solucion) > 1:
            puntos = []
            for (sr, sc) in ag.solucion:
                puntos.extend([sc * TAM + TAM // 2, sr * TAM + TAM // 2])
            self.canvas.create_line(*puntos, fill=COLOR_LINEA, width=4,
                                    smooth=True, joinstyle='round', capstyle='round')

            sr0, sc0 = ag.solucion[0]
            radio = TAM // 2 - 8
            self.canvas.create_oval(
                sc0 * TAM + 8, sr0 * TAM + 8,
                sc0 * TAM + TAM - 8, sr0 * TAM + TAM - 8,
                fill=COLOR_INICIO, outline=''
            )

        if not ag.terminado or ag.encontrado:
            ax = ag.c * TAM + TAM // 2
            ay = ag.r * TAM + TAM // 2
            ro = int(TAM * 0.30)
            self.canvas.create_oval(ax - ro, ay - ro, ax + ro, ay + ro,
                                    fill=COLOR_AGENTE, outline='')

    def _actualizar_ui(self):
        ag = self.agente
        self.lbl_visitas.config(text=str(len(ag.visitados)))
        self.lbl_pasos.config(text=str(ag.pasos))
        self.lbl_sol.config(text=str(len(ag.solucion)) if ag.solucion else '—')

        if ag.terminado:
            s = '¡Salida encontrada!' if ag.encontrado else 'Sin solución'
        elif self.corriendo:
            s = 'Explorando...'
        elif ag.pasos > 0:
            s = 'Pausado'
        else:
            s = 'Listo'
        self.lbl_estado.config(text=s)


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()