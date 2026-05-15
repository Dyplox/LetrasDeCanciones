#!/usr/bin/env python3
"""
Automation script to rename image and PDF files using Claude API.
Extracts the main title from each document and renames the file accordingly.
"""

import os
import re
import sys
import time
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

import anthropic
from dotenv import load_dotenv
from unidecode import unidecode
from PIL import Image


# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("ANTHROPIC_API_KEY")
INPUT_FOLDER = os.getenv("INPUT_FOLDER_PATH", "./input_files")
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILENAME_LENGTH = 255


class FileRenamer:
    """Handles file renaming using Claude API for title extraction."""

    def __init__(self, api_key: str, input_folder: str):
        """Initialize the renamer with API key and input folder."""
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in .env file or system environment."
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.input_folder = Path(input_folder)
        self.successful_renames = 0
        self.failed_renames = 0
        self.skipped_files = 0
        self.start_time = None

        # Create input folder if it doesn't exist
        self.input_folder.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, text: str) -> str:
        """
        Sanitize filename: remove accents, convert to Title Case with spaces,
        remove special characters, and ensure filesystem compatibility.
        """
        # Remove accents
        text = unidecode(text)

        # Remove special characters (keep only alphanumeric and spaces)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        # Normalize spaces (remove multiple consecutive spaces)
        text = re.sub(r'\s+', ' ', text)

        # Convert to Title Case
        text = text.title()

        # Remove leading/trailing spaces
        text = text.strip()

        # Ensure not empty
        if not text:
            text = "Unnamed"

        # Truncate to filesystem limit
        if len(text) > MAX_FILENAME_LENGTH:
            text = text[:MAX_FILENAME_LENGTH].rstrip()

        return text

    def extract_title_from_file(self, file_path: Path) -> Optional[str]:
        """
        Send file to Claude API and extract the main title.
        Returns the extracted title or None if extraction fails.
        """
        try:
            # Read file
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Prepare content based on file type
            extension = file_path.suffix.lower()

            if extension == ".pdf":
                # For PDFs, use base64 encoding
                base64_data = base64.standard_b64encode(file_data).decode("utf-8")
                content = [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract the main title or name from this document "
                            "(for example: song name in a musical score, document title, etc.). "
                            "Respond with ONLY the title, no explanations or additional text."
                        ),
                    },
                ]
            elif extension in {".jpg", ".jpeg", ".png"}:
                # Compress image if too large
                original_size = len(file_data)
                compressed_data = self._compress_image(file_data, file_path)

                if len(compressed_data) < original_size:
                    ratio = (1 - len(compressed_data) / original_size) * 100
                    print(f"  ℹ Compressed image by {ratio:.1f}%")

                # For images, use base64 encoding
                base64_data = base64.standard_b64encode(compressed_data).decode("utf-8")
                media_type = "image/jpeg" if extension in {".jpg", ".jpeg"} else "image/png"
                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract the main title or name from this image "
                            "(for example: song name, text, title, etc.). "
                            "Respond with ONLY the title, no explanations or additional text."
                        ),
                    },
                ]
            else:
                return None

            # Send message to Claude
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            )

            # Extract title from response
            title = message.content[0].text.strip()
            return title if title else None

        except anthropic.APIStatusError as e:
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                print(f"  ✗ API quota or rate limit exceeded")
            else:
                print(f"  ✗ API error: {e}")
            return None
        except (OSError, IOError) as e:
            print(f"  ✗ Cannot read file: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Unexpected error during extraction: {e}")
            return None

    def _is_uuid_filename(self, filename: str) -> bool:
        """Check if filename is a UUID (iPhone auto-generated naming pattern)."""
        # UUID format: 8-4-4-4-12 hex characters
        # Example: 9375781E-BE30-4EBB-92A4-C1CD2D56ED2B
        uuid_pattern = r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
        return bool(re.match(uuid_pattern, filename))

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        return mime_types.get(file_path.suffix.lower(), "application/octet-stream")

    def _compress_image(self, file_data: bytes, file_path: Path) -> bytes:
        """Compress image to fit within 5MB API limit (accounting for base64 overhead)."""
        # Target 3MB to account for base64 encoding overhead (~33%)
        max_size = 3.5 * 1024 * 1024  # 3.5 MB before base64

        if len(file_data) <= max_size:
            return file_data

        try:
            img = Image.open(BytesIO(file_data))

            # Convert RGBA to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                img = rgb_img

            # Step 1: Resize to reduce dimensions (most effective)
            max_dimension = 3000
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

            # Step 2: Compress with quality reduction
            quality = 75
            while quality > 5:
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=quality, optimize=True)
                compressed_data = buffer.getvalue()

                if len(compressed_data) <= max_size:
                    return compressed_data

                quality -= 5

            # Step 3: If still too large, resize more aggressively
            img.thumbnail((1500, 1500), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=40, optimize=True)
            compressed_data = buffer.getvalue()

            # Step 4: Last resort - very small and low quality
            if len(compressed_data) > max_size:
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=30, optimize=True)
                compressed_data = buffer.getvalue()

            return compressed_data

        except Exception as e:
            print(f"  ⚠ Warning: Could not compress image: {e}")
            return file_data

    def rename_file(self, old_path: Path, new_name: str) -> bool:
        """
        Rename file to new name, avoiding conflicts by adding suffixes.
        Returns True if successful, False otherwise.
        """
        try:
            extension = old_path.suffix.lower()
            new_name_with_ext = new_name + extension
            new_path = old_path.parent / new_name_with_ext

            # Handle filename conflicts
            counter = 1
            while new_path.exists():
                new_name_with_ext = f"{new_name}_{counter}{extension}"
                new_path = old_path.parent / new_name_with_ext
                counter += 1

            # Perform rename
            old_path.rename(new_path)
            print(f"  ✓ Renamed: {old_path.name} → {new_name_with_ext}")
            self.successful_renames += 1
            return True

        except OSError as e:
            print(f"  ✗ Cannot rename file: {e}")
            self.failed_renames += 1
            return False

    def process_files(self) -> None:
        """Process all valid files in the input folder."""
        self.start_time = time.time()

        print("\n" + "=" * 50)
        print("FILE RENAMING AUTOMATION - STARTING")
        print("=" * 50 + "\n")

        # Get list of files to process
        files_to_process = [
            f for f in self.input_folder.iterdir()
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
        ]

        if not files_to_process:
            print(f"No valid files found in {self.input_folder}")
            print("Supported formats: {', '.join(ALLOWED_EXTENSIONS)}\n")
            return

        print(f"Found {len(files_to_process)} file(s) to process\n")

        # Process each file
        for file_path in files_to_process:
            try:
                # Skip files that don't have UUID-style names (iPhone naming pattern)
                if not self._is_uuid_filename(file_path.stem):
                    print(f"Skipping: {file_path.name} (not auto-generated UUID)")
                    self.skipped_files += 1
                    continue

                print(f"Processing: {file_path.name}")

                # Extract title
                title = self.extract_title_from_file(file_path)
                if not title:
                    print(f"  ✗ Could not extract title from file")
                    self.failed_renames += 1
                    continue

                # Sanitize filename
                sanitized_name = self.sanitize_filename(title)

                # Rename file
                self.rename_file(file_path, sanitized_name)

            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")
                self.failed_renames += 1

        # Print summary
        self._print_summary()

    def _print_summary(self) -> None:
        """Print processing summary."""
        elapsed_time = time.time() - self.start_time
        total_processed = self.successful_renames + self.failed_renames

        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Skipped (non-UUID): {self.skipped_files}")
        print(f"Total processed: {total_processed}")
        print(f"Successful: {self.successful_renames}")
        print(f"Errors: {self.failed_renames}")
        print(f"Time elapsed: {elapsed_time:.2f}s")
        print("=" * 50 + "\n")


def main() -> None:
    """Main entry point."""
    try:
        if not API_KEY:
            print(
                "ERROR: ANTHROPIC_API_KEY not set.\n"
                "Please create a .env file with: ANTHROPIC_API_KEY=your_api_key\n"
                "Or set the environment variable: export ANTHROPIC_API_KEY=your_api_key"
            )
            sys.exit(1)

        renamer = FileRenamer(API_KEY, INPUT_FOLDER)
        renamer.process_files()

    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
