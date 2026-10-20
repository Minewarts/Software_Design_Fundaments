from abc import ABC, abstractmethod


class ServicioClima(ABC):
    @abstractmethod
    def historico_mensual(self, lugar: str, mes: int) -> dict:
        """Promedios históricos del mes (temp_max, temp_min, lluvia_mm, dias_lluvia)."""
