from fastapi import HTTPException
from pydantic import ValidationError


class CustomExceptionA(Exception):
    def __init__(self, message: str = "Bad request"):
        self.message = message
        self.status_code = 400


class CustomExceptionB(Exception):
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        self.status_code = 404


class ValidationErrorHandler(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        self.status_code = 422
