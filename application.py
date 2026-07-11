from flask import Flask, flash, render_template, request, redirect, url_for, session
from src.memory_allocation import Process, MemoryBlock, FirstFit, BestFit, WorstFit
from src.directions_translator import PageTable, PagingSimulator

app = Flask(__name__)
# Clave secreta requerida para manejar las sesiones de Flask de forma segura
app.secret_key = 'clave_secreta_fija_para_el_parcial_univalle'

# =====================================================================
# FUNCIONES AUXILIARES PARA LOGÍSITICA DE SESIÓN (PERSISTENCIA DE DATOS)
# =====================================================================

def serialize_contiguous_state(blocks: list[MemoryBlock], strategy_name: str) -> dict:
    """Serializa el estado del simulador de asignación contigua para guardarlo en la sesión.

    Args:
        blocks (list[MemoryBlock]): Lista de bloques de memoria actuales.
        strategy_name (str): Nombre de la estrategia activa.

    Returns:
        dict: Diccionario listo para ser almacenado en formato JSON en session.
    """
    serialized_blocks = []
    for b in blocks:
        # Serializa la lista completa de procesos que habitan cooperativamente en el bloque
        serialized_processes = [
            {'pid': p.process_id, 'size': p.size} for p in b.assigned_processes
        ]

        serialized_blocks.append({
            'start_address': b.start_address,
            'size': b.size,
            'assigned_processes': serialized_processes,
            'internal_frag': b.internal_fragmentation
        })

    return {'strategy': strategy_name, 'blocks': serialized_blocks}

def deserialize_contiguous_state(state: dict) -> tuple[list[MemoryBlock], str]:
    """Reconstruye el estado del simulador contiguo a partir de los datos de la sesión.

    Args:
        state (dict): Diccionario con el estado serializado guardado en session.

    Returns:
        tuple[list[MemoryBlock], str]: Tupla con la lista de bloques reconstruida y la estrategia.
    """
    if not state or 'blocks' not in state:
        return [], "First Fit"

    blocks = []
    for b_data in state['blocks']:
        block = MemoryBlock(
            start_address=b_data['start_address'],
            size=b_data['size']
        )

        # Reconstruye minuciosamente la lista de procesos asignados al bloque
        if 'assigned_processes' in b_data:
            for p_data in b_data['assigned_processes']:
                process = Process(process_id=p_data['pid'], size=p_data['size'])
                block.allocate(process)
        elif b_data.get('pid'):  # Soporte de compatibilidad por si acaso
            process = Process(process_id=b_data['pid'], size=b_data.get('proc_size', 0))
            block.allocate(process)

        blocks.append(block)

    return blocks, state.get('strategy', 'First Fit')

def serialize_paging_state(simulator: PagingSimulator) -> dict:
    """Serializa el estado del simulador de paginación virtual para la sesión.

    Args:
        simulator (PagingSimulator): Instancia activa del simulador de paginación.

    Returns:
        dict: Diccionario mapeado para la sesión.
    """
    serialized_frames = []
    for f in simulator.frames:
        serialized_frames.append({
            'frame_id': f.frame_id,
            'frame_size': f.frame_size,
            'pid': f.assigned_process_id,
            'page_num': f.assigned_page_number
        })

    # Serializar tablas de páginas por proceso
    serialized_tables = {}
    for pid, table in simulator.process_tables.items():
        serialized_tables[pid] = table.current_mappings

    return {
        'ram_size': len(simulator.frames) * simulator.page_size,
        'page_size': simulator.page_size,
        'frames': serialized_frames,
        'tables': serialized_tables
    }

def deserialize_paging_state(state: dict) -> PagingSimulator:
    """Reconstruye el simulador de paginación a partir del estado de la sesión.

    Args:
        state (dict): Datos crudos leídos de la sesión.

    Returns:
        PagingSimulator: Instancia con los marcos y tablas restauradas en memoria de objetos.
    """
    # Si por alguna razón la sesión está vacía, se evita un KeyError inicializando por defecto
    if not state or 'ram_size' not in state:
        return PagingSimulator(4096, 1024)

    sim = PagingSimulator(state['ram_size'], state['page_size'])

    # Restaurar estado real de los marcos físicos (RAM) tal como se guardaron
    for i, f_data in enumerate(state['frames']):
        if f_data['pid'] is not None:
            sim.frames[i].occupy(f_data['pid'], f_data['page_num'])

    for pid, mappings in state['tables'].items():
        # Crear la instancia de la tabla vacía directamente
        table = PageTable()
        typed_mappings = {int(k): v for k, v in mappings.items()}
        table.restore_mappings(typed_mappings)
        sim.process_tables[pid] = table

    return sim

# =====================================================================
# RUTAS DE LA INTERFAZ WEB CONTROLADORA
# =====================================================================

@app.route('/')
def index() -> str:
    """Ruta principal que renderiza el dashboard de la interfaz gráfica amigable."""
    # Inicializar estados por defecto si la sesión está limpia
    if 'contiguous' not in session:
        session['contiguous'] = serialize_contiguous_state([], 'First Fit')

    if 'paging' not in session:
        initial_paging_sim = PagingSimulator(4096, 1024)
        session['paging'] = serialize_paging_state(initial_paging_sim)

    # Reconstruir objetos para el renderizado dinámico
    c_blocks, c_strategy = deserialize_contiguous_state(session['contiguous'])
    p_sim = deserialize_paging_state(session['paging'])

    # ==========================================
    # PRINTS DE DIAGNÓSTICO
    # ==========================================
    print("\n=== [DIAGNÓSTICO SIMULADOR] ===")
    print(f"¿Cuántos bloques llegaron del backend?: {len(c_blocks)}")
    for i, b in enumerate(c_blocks):
        print(f"  Bloque {i}: Dir={b.start_address}, Tamaño={b.size}B, Procesos={b.assigned_processes}")
    print("================================\n")

    # ===================================================
    # NUEVO DIAGNÓSTICO IMP. 2: PAGINACIÓN VIRTUAL
    # ===================================================
    print("=== [DIAGNÓSTICO IMP. 2 - PAGINACIÓN] ===")
    print(f"Tamaño de Página: {p_sim.page_size}B | Total Marcos RAM: {len(p_sim.frames)}")
    occupied_frames = [f for f in p_sim.frames if not f.is_available]
    print(f"Marcos Ocupados: {len(occupied_frames)} / {len(p_sim.frames)}")
    for f in p_sim.frames:
        if not f.is_available:
            print(f"  [RAM] Marco {f.frame_id} -> Ocupado por: {f.assigned_process_id} (Pág. Lógica #{f.assigned_page_number})")
        else:
            print(f"  [RAM] Marco {f.frame_id} -> DISPONIBLE")

    print("Tablas de Páginas Activas en el Diccionario:")
    if p_sim.process_tables:
        for pid, table in p_sim.process_tables.items():
            print(f"  Proceso {pid}: Mapeos actuales -> {table.current_mappings}")
    else:
        print("  (Ninguna tabla de páginas registrada aún)")
    print("=========================================\n")

    # --- Cálculos Globales de Métricas Imp. 1 (Única ejecución limpia) ---
    free_blocks = [b for b in c_blocks if b.is_free]
    occupied_blocks = [b for b in c_blocks if not b.is_free]
    total_internal_frag = sum(b.internal_fragmentation for b in occupied_blocks)
    total_external_frag = sum(b.size for b in free_blocks)

    # Recuperar resultados de traducción de la MMU si existen en la sesión temporal
    mmu_result = session.pop('mmu_result', None)

    return render_template('index.html',
        c_blocks=c_blocks,
        c_strategy=c_strategy,
        free_blocks_count=len(free_blocks),
        occupied_blocks_count=len(occupied_blocks),
        internal_frag=total_internal_frag,
        external_frag=total_external_frag,
        p_sim=p_sim,
        mmu_result=mmu_result
    )

@app.route('/contiguous/init', methods=['POST'])
def contiguous_init():
    """Reinicializa el espacio de memoria contigua con las particiones ingresadas."""
    try:
        size_strings = request.form.get('sizes', '').split(',')
        strategy_name = request.form.get('strategy', 'First Fit')

        blocks = []
        current_address = 0
        for s in size_strings:
            if s.strip():
                size = int(s.strip())
                blocks.append(MemoryBlock(current_address, size))
                current_address += size

        session['contiguous'] = serialize_contiguous_state(blocks, strategy_name)
        session['contiguous_initialized'] = True
        session.modified = True  # Forzar a Flask a guardar los cambios mutados
    except (ValueError, IndexError):
        pass # Ignorar entradas con formatos erróneos para estabilidad del GUI

    return redirect(url_for('index'))

@app.route('/contiguous/allocate', methods=['POST'])
def contiguous_allocate():
    """Ejecuta el algoritmo de asignación contigua seleccionado para alojar un proceso."""
    pid = request.form.get('pid', '').strip()
    size_str = request.form.get('size', '0')
    size = int(size_str) if size_str.isdigit() else 0

    if pid and size > 0:
        blocks, strategy_name = deserialize_contiguous_state(session['contiguous'])

        for b in blocks:
            if any(p.process_id == pid for p in b.assigned_processes):
                flash(f"Error: El proceso {pid} ya se encuentra alojado en la memoria.", "error")
                return redirect(url_for('index'))

        process = Process(pid, size)
        # Mapear el string al objeto de estrategia heredado correspondiente
        strategy_map = {'First Fit': FirstFit(), 'Best Fit': BestFit(), 'Worst Fit': WorstFit()}
        strategy_algorithm = strategy_map.get(strategy_name, FirstFit())

        selected_block = strategy_algorithm.find_block(blocks, process)
        if selected_block:
            selected_block.allocate(process)
            session['contiguous'] = serialize_contiguous_state(blocks, strategy_name)
            session.modified = True  # Forzar persistencia de la cookie de sesión mutada
            flash(f"Proceso {pid} ({size}B) alojado con éxito usando {strategy_name}.", "success")
        else:
            flash(f"Fallo de Asignación: El proceso {pid} ({size}B) no cabe en ninguna partición libre/residual usando {strategy_name}.", "error")

    return redirect(url_for('index'))

@app.route('/contiguous/release/<int:start_address>')
def contiguous_release(start_address: int):
    """Libera un proceso de un bloque de memoria contigua mediante su dirección."""
    blocks, strategy_name = deserialize_contiguous_state(session['contiguous'])
    for b in blocks:
        if b.start_address == start_address:
            b.release()
            break
    session['contiguous'] = serialize_contiguous_state(blocks, strategy_name)
    session.modified = True  # Forzar persistencia de la cookie tras liberar

    return redirect(url_for('index'))

@app.route('/contiguous/reset_individual')
def contiguous_reset_individual():
    """Limpia únicamente el estado de la Asignación Contigua."""
    session['contiguous'] = serialize_contiguous_state([], 'First Fit')
    session['contiguous_initialized'] = False
    session.modified = True

    return redirect(url_for('index'))

@app.route('/paging/init', methods=['POST'])
def paging_init():
    """Reinicializa el sistema de hardware de paginación."""
    ram_size = int(request.form.get('ram_size', 4096))
    page_size = int(request.form.get('page_size', 1024))

    # Validar que el tamaño de página sea potencia de dos
    if page_size > 0 and (page_size & (page_size - 1)) == 0:
        sim = PagingSimulator(ram_size, page_size)
        session['paging'] = serialize_paging_state(sim)
        session.modified = True

    return redirect(url_for('index'))

@app.route('/paging/load', methods=['POST'])
def paging_load():
    """Crea un proceso en memoria virtual y le asigna marcos de página en la RAM."""
    pid = request.form.get('pid', '').strip()
    virtual_size = int(request.form.get('virtual_size', 0))

    if pid and virtual_size > 0:
        sim = deserialize_paging_state(session['paging'])
        if pid in sim.process_tables:
            flash(f"Error: El proceso {pid} ya está cargado en la Memoria Virtual.", "error")
            return redirect(url_for('index'))

        if sim.load_process(pid, virtual_size):
            session['paging'] = serialize_paging_state(sim)
            session.modified = True
            flash(f"Proceso {pid} ({virtual_size}B) cargado con éxito en Memoria Virtual y RAM.", "success")
        else:
            flash(f"Fallo de Paginación: Insuficientes marcos de página disponibles en la RAM para albergar {virtual_size}B del proceso {pid}.", "error")

    return redirect(url_for('index'))

@app.route('/paging/translate', methods=['POST'])
def paging_translate():
    """Simula la acción de hardware de la MMU traduciendo una dirección virtual."""
    pid = request.form.get('pid', '')
    virtual_address = int(request.form.get('virtual_address', 0))

    sim = deserialize_paging_state(session['paging'])
    table = sim.process_tables.get(pid)

    if table:
        phys_addr, page_num, offset, success = sim.mmu.translate(virtual_address, table)
        session['mmu_result'] = {
            'pid': pid,
            'virtual_address': virtual_address,
            'page_num': page_num,
            'offset': offset,
            'success': success,
            'physical_address': phys_addr
        }
        session.modified = True

    return redirect(url_for('index'))

@app.route('/paging/reset_individual')
def paging_reset_individual():
    """Limpia únicamente el estado de la Paginación Virtual."""
    initial_paging_sim = PagingSimulator(4096, 1024)
    session['paging'] = serialize_paging_state(initial_paging_sim)
    session.modified = True

    return redirect(url_for('index'))

@app.route('/reset')
def reset_all():
    """Limpia los registros de la sesión para reiniciar ambos simuladores a valores base."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Lanzar la aplicación en red abierta para correcta exposición del puerto en el contenedor Docker
    app.run(host='0.0.0.0', port=5000, debug=True)