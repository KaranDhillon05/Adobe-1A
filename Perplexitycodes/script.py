# Create the complete Adobe Hackathon PDF Processing System
import os

# Create directory structure for the complete solution
directories = [
    "adobe_pdf_processor",
    "adobe_pdf_processor/core",
    "adobe_pdf_processor/challenge1a", 
    "adobe_pdf_processor/challenge1b",
    "adobe_pdf_processor/utils",
    "adobe_pdf_processor/tests",
    "adobe_pdf_processor/schemas"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

print("✅ Project structure created successfully!")