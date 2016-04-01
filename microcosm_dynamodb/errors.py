"""
Persistence errors.

Errors define a `status_code` for each translation to HTTP (because REST)
but are not coupled with any HTTP library.

"""


class ModelIntegrityError(Exception):
    """
    An attempt to create or update a model violated a schema constraint.

    Usually the result of a programming error.

    """
    @property
    def status_code(self):
        # internal server error
        return 500


class ModelNotFoundError(Exception):
    """
    The queried or updated model did not exist.

    """
    @property
    def status_code(self):
        # not found
        return 404
