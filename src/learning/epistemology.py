class BayesianEngine:
    """
    Replaces flat confidence scores with probabilistic epistemology.
    Models beliefs using a Beta distribution parameterized by alpha (positive evidence)
    and beta (negative evidence/contradiction).
    This allows the twin to hold uncertainty and contradictory truths simultaneously.
    """
    def __init__(self):
        # Base prior: Alpha=1, Beta=1 (Uniform distribution, complete uncertainty)
        self.prior_alpha = 1.0
        self.prior_beta = 1.0

    def calculate_belief(self, alpha: float, beta: float) -> float:
        """
        Calculates the expected value (mean) of the Beta distribution,
        representing the current absolute belief in a concept.
        """
        return alpha / (alpha + beta)

    def calculate_uncertainty(self, alpha: float, beta: float) -> float:
        """
        Calculates the variance of the Beta distribution.
        High variance = high epistemic uncertainty (the twin knows it doesn't know).
        """
        return (alpha * beta) / (((alpha + beta) ** 2) * (alpha + beta + 1))

    def bayesian_update(self, current_alpha: float, current_beta: float, 
                        positive_evidence: float, negative_evidence: float) -> tuple[float, float]:
        """
        Updates the belief distribution based on new evidence.
        When new confirming data arrives, alpha increases.
        When contradictory data (or Nemesis paradoxes) arrive, beta increases.
        """
        new_alpha = current_alpha + positive_evidence
        new_beta = current_beta + negative_evidence
        return new_alpha, new_beta

    def compute_surprise(self, current_alpha: float, current_beta: float, new_evidence_val: float) -> float:
        """
        Calculates how surprising a new piece of evidence is compared to the current belief.
        If belief is highly certain (e.g., alpha=100, beta=1 -> belief=0.99) and 
        new_evidence_val is 0.0 (total contradiction), surprise is massive.
        """
        current_belief = self.calculate_belief(current_alpha, current_beta)
        # Simple absolute error between expected value and new observation
        surprise = abs(current_belief - new_evidence_val)
        return surprise
