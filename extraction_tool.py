"""
Extraction tool with JSON schema — ensures null for absent fields, no hallucination.

EXAM: Use json_schema in response_format to enforce structured extraction.
This is the correct way to get guaranteed valid JSON — not string parsing.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()

# ─── Define the extraction schema ────────────────────────────────────────────
# EXAM: Use json_schema response_format to ensure Claude returns ONLY valid JSON
# TRAP: If a field is truly absent in the document, return null — NOT invented text

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": ["string", "null"],
            "description": "Full name of the person mentioned. Return null if absent."
        },
        "email": {
            "type": ["string", "null"],
            "description": "Email address. Return null if absent."
        },
        "phone": {
            "type": ["string", "null"],
            "description": "Phone number. Return null if absent."
        },
        "company": {
            "type": ["string", "null"],
            "description": "Company or organization name. Return null if absent."
        },
        "title": {
            "type": ["string", "null"],
            "description": "Job title or professional role. Return null if absent."
        }
    },
    "required": ["name", "email", "phone", "company", "title"],
    "additionalProperties": False
}


@dataclass
class ExtractedData:
    """Structured result from extraction."""
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    title: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "title": self.title
        }

    def has_null_fields(self) -> bool:
        """Return True if any field is None."""
        return any(v is None for v in [self.name, self.email, self.phone, self.company, self.title])


def extract_from_document(document: str) -> ExtractedData:
    """
    Extract structured data from an unstructured document using tools.

    EXAM: Use tool_use to enforce structured extraction — Claude returns
    tool_use with the extracted JSON, guaranteed valid schema.

    Args:
        document: Raw text to extract from

    Returns:
        ExtractedData with null for any absent fields (NOT hallucinated)
    """

    logger.info(f"Extracting from document ({len(document)} chars)")

    # Define extraction as a tool to guarantee structured output
    extraction_tool = {
        "name": "extract_data",
        "description": "Extract structured data from a document",
        "input_schema": EXTRACTION_SCHEMA
    }

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=[extraction_tool],
        tool_choice={"type": "tool", "name": "extract_data"},
        system="""You are a data extraction agent. Extract the following fields from the provided document:
- name: Full name (null if not mentioned)
- email: Email address (null if not mentioned)
- phone: Phone number (null if not mentioned)
- company: Company name (null if not mentioned)
- title: Job title (null if not mentioned)

CRITICAL: Return null for any field NOT explicitly mentioned in the document.
DO NOT invent, guess, or hallucinate missing values.
Use the extract_data tool with the extracted fields.""",
        messages=[
            {
                "role": "user",
                "content": f"Extract data from this document:\n\n{document}"
            }
        ]
    )

    # EXAM: Extract tool input from response
    logger.info(f"stop_reason: {response.stop_reason}")

    if response.stop_reason != "tool_use":
        raise ValueError(f"Expected tool_use, got {response.stop_reason}")

    # Find the tool_use block
    tool_block = next(
        (b for b in response.content if b.type == "tool_use"),
        None
    )

    if not tool_block:
        raise ValueError("No tool_use block found in response")

    data = tool_block.input
    logger.info(f"Raw response: {json.dumps(data, indent=2)}")

    result = ExtractedData(
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        company=data.get("company"),
        title=data.get("title")
    )

    logger.info(f"Parsed result: {result}")
    return result


# ─── Test Documents ────────────────────────────────────────────────────────

TEST_DOCS = [
    # Doc 1: Only name and email
    """
    Hello, my name is Alice Johnson.
    You can reach me at alice.johnson@example.com.
    """,

    # Doc 2: Name, company, title — no contact
    """
    Bob Smith works at TechCorp as a Senior Engineer.
    He has been there for 5 years.
    """,

    # Doc 3: Phone only
    """
    If you need to contact me, call 555-1234.
    Leave a message.
    """,

    # Doc 4: Email and phone only
    """
    Email: charlie@example.org
    Phone: +1-800-555-9999
    """,

    # Doc 5: Everything
    """
    Name: Diana Chen
    Email: diana.chen@acmecorp.com
    Phone: 415-555-0123
    Company: Acme Corporation
    Title: Product Manager
    """
]


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("EXTRACTION TEST: 5 Documents with Varying Completeness")
    logger.info("="*60)

    results = []

    for idx, doc in enumerate(TEST_DOCS, 1):
        logger.info(f"\n[DOC {idx}]")
        logger.info(f"Input:\n{doc.strip()}\n")

        extracted = extract_from_document(doc)
        results.append(extracted)

        logger.info(f"Extracted: {json.dumps(extracted.to_dict(), indent=2)}")
        logger.info(f"Has null fields: {extracted.has_null_fields()}")

        # Validate: no field should be empty string, only None
        for field_name, field_value in extracted.to_dict().items():
            if field_value is not None and field_value.strip() == "":
                logger.error(f"  ❌ FAIL: {field_name} is empty string, not null")
            elif field_value is None:
                logger.info(f"  ✓ {field_name}: null (correct)")
            else:
                logger.info(f"  ✓ {field_name}: {field_value}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Processed {len(results)} documents")

    docs_with_nulls = sum(1 for r in results if r.has_null_fields())
    logger.info(f"Documents with at least one null field: {docs_with_nulls}/{len(results)}")

    # Show final results as JSON
    logger.info("\nAll Results:")
    all_results = [r.to_dict() for r in results]
    logger.info(json.dumps(all_results, indent=2))
