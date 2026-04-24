"""
Test suite for extraction_tool.py — specifically testing 5 documents where fields are absent.
Ensures that the tool returns null for missing fields and does not hallucinate.
"""

from unittest.mock import Mock, patch
import pytest
from extraction_tool import extract_from_document

class TestAbsentFields:
    """Test cases for documents with absent fields."""

    @patch("extraction_tool.client.messages.create")
    def test_doc_1_name_email_only(self, mock_create: Mock) -> None:
        """Test with only name and email."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": "Alice Wonderland",
                    "email": "alice@rabbit.hole",
                    "phone": None,
                    "company": None,
                    "title": None
                }
            )
        ]
        mock_create.return_value = mock_response

        doc = "Alice Wonderland can be reached at alice@rabbit.hole."
        result = extract_from_document(doc)
        
        assert result.name == "Alice Wonderland"
        assert result.email == "alice@rabbit.hole"
        assert result.phone is None
        assert result.company is None
        assert result.title is None

    @patch("extraction_tool.client.messages.create")
    def test_doc_2_company_title_only(self, mock_create: Mock) -> None:
        """Test with only company and title."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": None,
                    "email": None,
                    "phone": None,
                    "company": "GloboCorp",
                    "title": "Lead Architect"
                }
            )
        ]
        mock_create.return_value = mock_response

        doc = "The Lead Architect at GloboCorp is currently hiring."
        result = extract_from_document(doc)
        
        assert result.name is None
        assert result.email is None
        assert result.phone is None
        assert result.company == "GloboCorp"
        assert result.title == "Lead Architect"

    @patch("extraction_tool.client.messages.create")
    def test_doc_3_phone_only(self, mock_create: Mock) -> None:
        """Test with only phone."""
        mock_response = Mock()
        mock_response.stop_reason = "tool_use"
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": None,
                    "email": None,
                    "phone": "555-0199",
                    "company": None,
                    "title": None
                }
            )
        ]
        mock_create.return_value = mock_response

        doc = "Please call 555-0199 for more details."
        result = extract_from_document(doc)
        
        assert result.name is None
        assert result.email is None
        assert result.phone == "555-0199"
        assert result.company is None
        assert result.title is None

    @patch("extraction_tool.client.messages.create")
    def test_doc_4_name_title_only(self, mock_create: Mock) -> None:
        """Test with only name and title."""
        mock_response = Mock()
        mock_reason = "tool_use"
        mock_response.stop_reason = mock_reason
        mock_response.content = [
            Mock(
                type="tool_use",
                input={
                    "name": "John Doe",
                    "email": None,
                    "phone": None,
                    "company": None,
                    "title": "Software Engineer"
                }
            )
        ]
        mock_create.return_value = mock_response

        doc = "John Doe is a Software Engineer."
        result = extract_from_document(doc)
        
        assert result.name == "John Doe"
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title == "Software Engineer"

    @patch("extraction_tool.client.messages.create")
    def test_doc_5_all_missing(self, mock_create: Mock) -> None:
        """Test with no relevant information."""
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

        doc = "The weather is nice today, but no one is mentioned here."
        result = extract_from_document(doc)
        
        assert result.name is None
        assert result.email is None
        assert result.phone is None
        assert result.company is None
        assert result.title is None
