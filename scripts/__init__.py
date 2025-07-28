"""
Hace que `scripts` sea un paquete importable desde los DAGs y los tests.

Aquí podemos reexportar utilidades para que los tests no tengan que
importar funciones privadas desde varios módulos.

from .transform_to_3nf import fix_encoding, clean_location, clean_schedule

__all__ = ["fix_encoding", "clean_location", "clean_schedule"]
"""
