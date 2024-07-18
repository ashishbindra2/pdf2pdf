import os
pdf_directory = r"static\pdf\01 Adsolut initiatie"
pdf_files = sorted([os.path.join(pdf_directory, f) for f in os.listdir(pdf_directory) if f.endswith('.pdf')])
print(pdf_files)
# print(os.listdir(r"static\pdf\01 Adsolut initiatie"))