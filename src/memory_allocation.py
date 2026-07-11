from abc import ABC, abstractmethod
from typing import List, Optional

class Process:
    """Representa un proceso del sistema operativo que requiere espacio en memoria física."""

    def __init__(self, process_id: str, size: int) -> None:
        """Inicializa una instancia de la clase Process.

        Args:
            process_id (str): Identificador único del proceso (ej: 'PID1').
            size (int): Tamaño total requerido por el proceso en bytes.
        """
        self.process_id: str = process_id
        self.size: int = size

    def __repr__(self) -> str:
        return f"Process(id={self.process_id}, size={self.size}B)"

class MemoryBlock:
    """Representa una partición o bloque contiguo de la memoria física."""

    def __init__(self, start_address: int, size: int) -> None:
        """Inicializa una partición de memoria orientada a asignación contigua.

        Args:
            start_address (int): Dirección física inicial del bloque.
            size (int): Capacidad total del bloque de memoria en bytes.
        """
        self.start_address: int = start_address
        self.size: int = size
        # Lista para cohabitación de múltiples procesos en la partición
        self.assigned_processes: List[Process] = []

    @property
    def used_space(self) -> int:
        """Calcula el espacio total ocupado por los procesos dentro del bloque.

        Returns:
            int: Cantidad de bytes ocupados por los procesos alojados.
        """
        return sum(process.size for process in self.assigned_processes)

    @property
    def remaining_space(self) -> int:
        """Calcula la capacidad residual disponible en el bloque de memoria.

        Returns:
            int: Espacio restante en bytes.
        """
        return self.size - self.used_space

    @property
    def internal_fragmentation(self) -> int:
        """Determina la fragmentación interna acumulada en el bloque.

        Returns:
            int: El espacio sobrante si el bloque está ocupado, o 0 si está libre.
        """
        if self.is_free:
            return 0
        return self.remaining_space

    @property
    def is_free(self) -> bool:
        """Determina si el bloque de memoria está totalmente disponible.

        Returns:
            bool: True si el bloque no tiene procesos asignados, False de lo contrario.
        """
        return len(self.assigned_processes) == 0

    def allocate(self, process: Process) -> None:
        """Aloja un proceso en el bloque aprovechando el espacio residual interno.

        Args:
            process (Process): El objeto proceso a alojar en esta partición.
        """
        self.assigned_processes.append(process)

    def release(self) -> None:
        """Desaloja todos los procesos asignados y restablece el bloque a su estado inicial."""
        self.assigned_processes = []

    def __repr__(self) -> str:
        if self.is_free:
            status = "LIBRE"
        else:
            p_ids = ", ".join([p.process_id for p in self.assigned_processes])
            status = f"OCUPADO por [{p_ids}] (Sobra: {self.internal_fragmentation}B)"

        return f"Block [{self.start_address}-{self.start_address + self.size}] -> {status}"

class AllocationStrategy(ABC):
    """Clase base abstracta que establece el contrato para los algoritmos de asignación."""

    @abstractmethod
    def find_block(self, blocks: List[MemoryBlock], process: Process) -> Optional[MemoryBlock]:
        """Algoritmo de búsqueda de un bloque óptimo para el proceso entrante.

        Args:
            blocks (List[MemoryBlock]): Lista actual de todos los bloques de memoria.
            process (Process): Proceso que solicita alojamiento.

        Returns:
            Optional[MemoryBlock]: El bloque seleccionado o None si no hay espacio adecuado.
        """
        pass

class FirstFit(AllocationStrategy):
    """Implementación del algoritmo Primer Ajuste (First-Fit)."""

    def find_block(self, blocks: List[MemoryBlock], process: Process) -> Optional[MemoryBlock]:
        # Evalúa basándose en el espacio restante real del bloque
        for block in blocks:
            if block.remaining_space >= process.size:
                return block

        return None

class BestFit(AllocationStrategy):
    """Implementación del algoritmo Mejor Ajuste (Best-Fit)."""

    def find_block(self, blocks: List[MemoryBlock], process: Process) -> Optional[MemoryBlock]:
        best_block: Optional[MemoryBlock] = None
        for block in blocks:
            if block.remaining_space >= process.size:
                if best_block is None or block.remaining_space < best_block.remaining_space:
                    best_block = block

        return best_block

class WorstFit(AllocationStrategy):
    """Implementación del algoritmo Peor Ajuste (Worst-Fit)."""

    def find_block(self, blocks: List[MemoryBlock], process: Process) -> Optional[MemoryBlock]:
        worst_block: Optional[MemoryBlock] = None
        for block in blocks:
            if block.remaining_space >= process.size:
                if worst_block is None or block.remaining_space > worst_block.remaining_space:
                    worst_block = block

        return worst_block