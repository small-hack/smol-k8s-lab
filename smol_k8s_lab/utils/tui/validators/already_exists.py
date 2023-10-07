from textual.validation import Validator, ValidationResult


# A custom validator to check if the name is already in use
class CheckIfNameAlreadyInUse(Validator):

    def __init__(self, cluster_names: list) -> None:
        super().__init__()
        self.cluster_names = cluster_names

    def validate(self, value: str) -> ValidationResult:
        """Check if a string is already in use as a clustername."""
        if value in self.cluster_names:
            return self.failure("That cluster name is already in use 🫨")
        else:
            return self.success()
