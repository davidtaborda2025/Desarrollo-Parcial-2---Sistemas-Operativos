from typing import List, Optional, Dict, Tuple

class PageFrame:
    """Representa un Marco de Página (Page Frame) dentro de la memoria física real (RAM)."""

    def __init__(self, frame_id: int, frame_size: int) -> None:
        """Inicializa un marco físico de tamaño fijo.

        Args:
            frame_id (int): Índice identificador del marco en la RAM.
            frame_size (int): Tamaño fijo del marco en bytes.
        """
        self.frame_id: int = frame_id
        self.frame_size: int = frame_size
        self.assigned_process_id: Optional[str] = None
        self.assigned_page_number: Optional[int] = None

    @property
    def is_available(self) -> bool:
        """Verifica si el marco físico se encuentra libre.

        Returns:
            bool: True si está libre, False si está ocupado por una página.
        """
        return self.assigned_process_id is None

    def occupy(self, process_id: str, page_number: int) -> None:
        """Asigna una página virtual a este marco físico.

        Args:
            process_id (str): ID del proceso dueño de la página.
            page_number (int): Número de la página mapeada.
        """
        self.assigned_process_id = process_id
        self.assigned_page_number = page_number

    def release(self) -> None:
        """Libera el marco físico borrando sus registros de asignación."""
        self.assigned_process_id = None
        self.assigned_page_number = None

class PageTable:
    """Estructura de datos encargada de mapear números de páginas virtuales a marcos físicos."""

    def __init__(self) -> None:
        """Inicializa una tabla de páginas vacía para un proceso."""
        self._entries: Dict[int, int] = {}

    def map_page(self, page_number: int, frame_id: int) -> None:
        """Registra la asociación entre una página lógica y un marco de RAM real.

        Args:
            page_number (int): Índice de la página virtual.
            frame_id (int): Identificador del marco físico asignado.
        """
        self._entries[page_number] = frame_id

    def get_frame(self, page_number: int) -> Optional[int]:
        """Consulta si la página está cargada en la RAM física.

        Args:
            page_number (int): Índice de la página virtual a consultar.

        Returns:
            Optional[int]: El ID del marco correspondiente, o None si ocurre un Page Fault.
        """
        return self._entries.get(page_number)

    def clear(self) -> None:
        """Limpia la totalidad de los mapeos registrados en la tabla."""
        self._entries.clear()

    @property
    def current_mappings(self) -> Dict[int, int]:
        """Retorna una copia de las traducciones vigentes de la tabla.

        Returns:
            Dict[int, int]: Mapa actual de Página Virtual a Marco Físico.
        """
        return self._entries.copy()

    def restore_mappings(self, mappings: Dict[int, int]) -> None:
        """Restaura de forma segura los mapeos de la tabla desde un diccionario.

        Args:
            mappings (Dict[int, int]): Diccionario de traducción página-marco.
        """
        self._entries = mappings.copy()

class Mmu:
    """Memory Management Unit: Hardware simulado para la descomposición y traducción de direcciones."""

    def __init__(self, page_size: int) -> None:
        """Inicializa la unidad de gestión de memoria con un tamaño fijo de página.

        Args:
            page_size (int): Tamaño predefinido de las páginas y marcos en bytes.
        """
        self._page_size: int = page_size

    def decompose_virtual_address(self, virtual_address: int) -> Tuple[int, int]:
        """Realiza la descomposición matemática de una dirección lógica.

        Args:
            virtual_address (int): Dirección virtual generada por la CPU.

        Returns:
            Tuple[int, int]: Una tupla que contiene (número_de_página, desplazamiento).
        """
        page_number = virtual_address // self._page_size
        offset = virtual_address % self._page_size

        return page_number, offset

    def translate(self, virtual_address: int, page_table: PageTable) -> Tuple[Optional[int], int, int, bool]:
        """Traduce de forma directa una dirección virtual a una dirección física real.

        Args:
            virtual_address (int): Dirección lógica a mapear.
            page_table (PageTable): Tabla de páginas activa del proceso consultante.

        Returns:
            Tuple[Optional[int], int, int, bool]: Tupla con (dirección_física, página, offset, éxito).
        """
        page_number, offset = self.decompose_virtual_address(virtual_address)
        frame_id = page_table.get_frame(page_number)

        if frame_id is None:
            return None, page_number, offset, False  # Ocurre un Fallo de Página (Page Fault)

        physical_address = (frame_id * self._page_size) + offset

        return physical_address, page_number, offset, True

class PagingSimulator:
    """Orquestador maestro que representa el subsistema de Memoria Virtual y RAM por Paginación."""

    def __init__(self, total_ram_size: int, page_size: int) -> None:
        """Configura el entorno de memoria física fragmentada en marcos fijos.

        Args:
            total_ram_size (int): Tamaño total de la memoria RAM física en bytes.
            page_size (int): Tamaño de página/marco seleccionado (potencia de 2).
        """
        self.page_size: int = page_size
        self.mmu: Mmu = Mmu(page_size)
        self.frames: List[PageFrame] = []

        num_frames = total_ram_size // page_size
        for i in range(num_frames):
            self.frames.append(PageFrame(frame_id=i, frame_size=page_size))

        self.process_tables: Dict[str, PageTable] = {}

    def load_process(self, process_id: str, virtual_size: int) -> bool:
        """Reserva marcos físicos para el espacio de direccionamiento virtual del proceso.

        Args:
            process_id (str): Identificador único del proceso.
            virtual_size (int): Espacio lógico total requerido por el proceso en bytes.

        Returns:
            bool: True si la RAM física tiene marcos suficientes, False de lo contrario.
        """
        required_pages = (virtual_size + self.page_size - 1) // self.page_size
        available_frames = [f for f in self.frames if f.is_available]

        if len(available_frames) < required_pages:
            return False

        table = PageTable()
        for page_num in range(required_pages):
            frame = available_frames.pop(0)
            frame.occupy(process_id, page_num)
            table.map_page(page_num, frame.frame_id)

        self.process_tables[process_id] = table

        return True