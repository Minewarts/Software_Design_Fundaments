from abc import ABC, abstractmethod


class Traductor(ABC):
    @abstractmethod
    def traducir(self, textos: dict[str, str], idioma: str) -> dict[str, str]:
        """Traduce los valores conservando las claves."""
