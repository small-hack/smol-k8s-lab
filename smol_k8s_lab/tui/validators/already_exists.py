from textual.validation import Validator, ValidationResult


# A custom validator to check if the name is already in use
class CheckIfNameAlreadyInUse(Validator):

    def __init__(self, global_params: list) -> None:
        super().__init__()
        self.params = global_params

    def validate(self, value: str) -> ValidationResult:
        """Check if a string is already in use as an app name."""
        if value in self.params and value != "kubelet-arg":
            return self.failure("That name is already in use 🫨")
        else:
            return self.success()
