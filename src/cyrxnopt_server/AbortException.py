class AbortException(BaseException):
    """Exception raised when an optimization is aborted."""

    def __init__(self) -> None:
        self.value = "Optimization was aborted by a remote connection."

    def __str__(self) -> str:
        """Determines how this class is converted into a string.

        :return: String representation of this class.
        :rtype: str
        """

        return self.value


if __name__ == "__main__":
    raise (AbortException())
