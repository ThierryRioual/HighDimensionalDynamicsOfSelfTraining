import torch
from abc import ABC, abstractmethod

class LossFunction(ABC):
    @abstractmethod
    def evaluate(self, r: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Return the sum of per-observation losses."""
        pass

    @abstractmethod
    def gradient(self, r: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Return the per-observation score derivatives."""
        pass

class Penalty(ABC):
    @abstractmethod
    def evaluate(self, w: torch.Tensor) -> torch.Tensor:
        """Returns the penalization value R(w)."""
        pass

    @abstractmethod
    def gradient(self, w: torch.Tensor) -> torch.Tensor:
        """Returns the subgradient/gradient vector \nabla R(w)."""
        pass

class LogisticLoss(LossFunction):
    def evaluate(self, r: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        margins = y * r
        return torch.sum(torch.logaddexp(torch.zeros_like(margins), -margins))

    def gradient(self, r: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        margins = y * r
        probabilities = torch.sigmoid(-margins)
        grad = -y * probabilities
        return grad

class RidgePenalty(Penalty):
    def evaluate(self, w: torch.Tensor) -> torch.Tensor:
        return 0.5 * torch.sum(w ** 2)

    def gradient(self, w: torch.Tensor) -> torch.Tensor:
        return w

class HardSelection:
    """Inclusive confidence selection on independently configured raw margins."""

    def __call__(self, preactivation: torch.Tensor, pos_margin: float, neg_margin: float) -> torch.Tensor:
        selected = (preactivation >= pos_margin) | (preactivation <= neg_margin)
        return selected.to(dtype=preactivation.dtype)
