"""
Test suite for extraction_tool.py — verify null handling for absent fields.

EXAM: Mock all external API calls — never test against live API.
Use fixtures for common setup.
"""

import json
from unittest.mock import Mock, patch
import pytest

from extraction_tool import ExtractedData, extract_from_document, EXTRACTION_SCHEMA


class TestExtractedData:
    """Test the ExtractedData dataclass."""

    def test_to_dict_all_fields_present(self) -> None:
        """All fields present — should serialize correctly."""
        data = ExtractedData(
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-1234",
            company="TechCorp",
            title="Engineer"
        )
        result = data.to_dict()
        assert result["name"] == "Alice Johnson"
        assert result["email"] == "alice@example.com"
        assert result["phone"] == "555-1234"
        assert result["company"] == "TechCorp"
        assert result["title"] == "Engineer"

    def test_to_dict_with_nulls(self) -> None:
        """Some fields null — should preserve null values, not convert to empty string."""
        data = ExtractedData(
            name="Bob Smith",
            email=None,
            phone=None,
            company="AcmeCorp",
            title=None
        )
        result = data.to_dict()
        assert result["name"] == "Bob Smith"
        assert result["email"] is None  # EXAM: Must be None, not ""
        assert result["phone"] is None
        assert result["company"] == "AcmeCorp"
        assert result["title"] is None

    def test_has_null_fields_true(self) -> None:
        """Should detect presence of at least one null field."""
        data = ExtractedData(
            name="Charlie",
            email=None,
            phone="555-9999",
            company=None,
            title="Manager"
        )
        assert data.has_null_fields() is True

    def test_has_null_fields_false(self) -> None:
        """All fields present — should return False."""
        data = ExtractedData(
            name="Diana",
            email="diana@example.com",
            phone="555-5555",
            company="XyzCorp",
            title="Director"
        )
        assert data.has_null_fields() is False

    def test_has_null_fields_all_null(self) -> None:
        """All fields null — should return True."""
        data = ExtractedData(
            name=None,
            email=None,
            phone=None,
            company=None,
            title=None
        )
        assert data.has_null_fields() is True


class TestExtraction:
    """Test the extraction_from_document function."""

    @patch("extraction_tool.client.messages.create")
    def test_extraction_all_fields_present(self, mock_create: Mock) -> None:
        """Document with all fields present."""
        # Mock the API response with all fields
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": "Alice Johnson",
                    "email": "alice@example.com",
                    "phone": "555-1234",
                    "company": "TechCorp",
                    "title": "Senior Engineer"
                }
            )
        ]
        mock_create.return_value = mock_response

        result = extract_from_document("Alice Johnson works at TechCorp...")
        assert result.name == "Alice Johnson"
        assert result.email == "alice@example.com"
        assert result.phone == "555-1234"
        assert result.company == "TechCorp"
        assert result.title == "Senior Engineer"
        assert result.has_null_fields() is False

    @patch("extraction_tool.client.messages.create")
    def test_extraction_missing_email_and_phone(self, mock_create: Mock) -> None:
        """Document missing email and phone — should return null, not invent."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": "Bob Smith",
                    "email": None,
                    "phone": None,
                    "company": "AcmeCorp",
                    "title": "Manager"
                }
            )
        ]
        mock_create.return_value = mock_response

        result = extract_from_document("Bob Smith is a Manager at AcmeCorp.")
        assert result.name == "Bob Smith"
        assert result.email is None  # EXAM: CRITICAL — not ""
        assert result.phone is None  # EXAM: CRITICAL — not ""
        assert result.company == "AcmeCorp"
        assert result.title == "Manager"
        assert result.has_null_fields() is True

    @patch("extraction_tool.client.messages.create")
    def test_extraction_only_name(self, mock_create: Mock) -> None:
        """Document with only name — everything else null."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": "Charlie Brown",
                    "email": None,
                    "phone": None,
                    "company": None,
                    "title": None
                }
            )
        ]
        mock_create.return_value = mock_response

        result = extract_from_document("My name is Charlie Brown.")
        assert result.name == "Charlie Brown"
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title is None
        assert result.has_null_fields() is True

    @patch("extraction_tool.client.messages.create")
    def test_extraction_all_null(self, mock_create: Mock) -> None:
        """Document with no extractable data — all fields null."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": None,
                    "email": None,
                    "phone": None,
                    "company": None,
                    "title": None
                }
            )
        ]
        mock_create.return_value = mock_response

        result = extract_from_document("This is just random text with no details.")
        assert result.name is None
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title is None
        assert result.has_null_fields() is True

    @patch("extraction_tool.client.messages.create")
    def test_extraction_wrong_stop_reason(self, mock_create: Mock) -> None:
        """API returns end_turn instead of tool_use — should error."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = []
        mock_create.return_value = mock_response

        with pytest.raises(ValueError, match="Expected tool_use"):
            extract_from_document("Some document")

    @patch("extraction_tool.client.messages.create")
    def test_extraction_no_tool_block(self, mock_create: Mock) -> None:
        """Response has tool_use stop_reason but no tool_use block — should error."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = []
        mock_create.return_value = mock_response

        with pytest.raises(ValueError, match="No tool_use block"):
            extract_from_document("Some document")


class TestExtractionSchema:
    """Test the JSON schema definition."""

    def test_schema_has_required_fields(self) -> None:
        """Schema must require all 5 fields."""
        assert "required" in EXTRACTION_SCHEMA
        required = EXTRACTION_SCHEMA["required"]
        assert "name" in required
        assert "email" in required
        assert "phone" in required
        assert "company" in required
        assert "title" in required
        assert len(required) == 5

    def test_schema_fields_allow_null(self) -> None:
        """Each field must allow null type."""
        for field_name in ["name", "email", "phone", "company", "title"]:
            field_def = EXTRACTION_SCHEMA["properties"][field_name]
            # Type can be ["string", "null"] or ["null", "string"]
            assert "null" in field_def["type"]
            assert "string" in field_def["type"]

    def test_schema_no_additional_properties(self) -> None:
        """Schema should not allow extra fields."""
        assert EXTRACTION_SCHEMA.get("additionalProperties") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
