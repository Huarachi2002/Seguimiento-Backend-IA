"""
Unit Tests for Validators
==========================

Tests unitarios para las funciones de validación.
"""

import pytest
from app.utils.validators import (
    validate_phone_number,
    format_phone_number,
    extract_last_four_digits,
    truncate_text,
    sanitize_input
)


class TestPhoneValidation:
    """Tests para validación de números telefónicos"""
    
    def test_valid_phone_numbers(self):
        """Números válidos deben pasar la validación"""
        assert validate_phone_number("+59170123456") == True
        assert validate_phone_number("59170123456") == True
        assert validate_phone_number("70123456") == True
    
    def test_invalid_phone_numbers(self):
        """Números inválidos deben fallar"""
        assert validate_phone_number("123") == False
        assert validate_phone_number("") == False
        assert validate_phone_number("abc") == False
    
    def test_format_phone_number(self):
        """Formateo debe normalizar números"""
        assert format_phone_number("70123456") == "+59170123456"
        assert format_phone_number("+59170123456") == "+59170123456"
        assert format_phone_number("591 701 23456") == "+59170123456"
    
    def test_extract_last_four_digits(self):
        """Extracción de últimos 4 dígitos"""
        assert extract_last_four_digits("+59170123456") == "3456"
        assert extract_last_four_digits("123") == "123"


class TestTextUtils:
    """Tests para utilidades de texto"""
    
    def test_truncate_text(self):
        """Truncar texto largo"""
        text = "A" * 200
        truncated = truncate_text(text, max_length=50)
        assert len(truncated) == 50
        assert truncated.endswith("...")
    
    def test_truncate_short_text(self):
        """Texto corto no debe truncarse"""
        text = "Hola"
        assert truncate_text(text, max_length=50) == "Hola"
    
    def test_sanitize_input(self):
        """Sanitizar input peligroso"""
        dangerous = "Test\x00with null"
        sanitized = sanitize_input(dangerous)
        assert "\x00" not in sanitized
    
    def test_sanitize_multiple_spaces(self):
        """Múltiples espacios deben reducirse"""
        text = "Hola     mundo"
        assert sanitize_input(text) == "Hola mundo"


# Para ejecutar: pytest tests/unit/test_validators.py -v
