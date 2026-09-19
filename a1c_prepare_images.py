#!/usr/bin/env python3

import shutil
from config import PATH
from helper import log_section, convert_pdf_to_png, convert_mps_to_png


@log_section
def prepare_images():
    # Obrazki leza w podkatalogach dropu, a redakcja co numer wymysla nowa
    # nazwe (art, rys, stale, graphics, ilustracje, doppler...) - zamiast
    # dopisywac je do whitelisty skanujemy WSZYSTKIE podkatalogi got/.
    # Sam top-level got/ pomijamy swiadomie: leza tam PDF-y calego numeru
    # (2026-09-delta.pdf, ...-delta_press.pdf, po kilkanascie MB), ktorych
    # nie chcemy konwertowac do PNG ani wysylac na serwer.
    source_folders = sorted(
        d.name for d in PATH.SOURCE.iterdir() if d.is_dir()
    )
    print(f"# Scanning subfolders: {', '.join(source_folders)}")
    pdf_files = []
    mps_files = []
    copied_files_count = 0
    converted_files_count = 0

    for source_folder in source_folders:
        source_path = PATH.SOURCE / source_folder
        if source_path.exists():
            for file in source_path.rglob("*"):
                if file.is_file():
                    suffix = file.suffix.lower()
                    if suffix in {".png", ".jpg", ".jpeg"}:
                        dest_path = PATH.FIGURES / file.name
                        shutil.copy2(file, dest_path)
                        copied_files_count += 1
                        print(f"# Copied {dest_path}")
                    elif suffix == ".pdf":
                        pdf_files.append(file)
                    # MetaPost: przegladarka nie wyswietli .mps, a artykul
                    # odwoluje sie do niego jak do zwyklego obrazka (2026-10,
                    # got/saper/). Konwersja do PNG + podmiana rozszerzenia w
                    # \includegraphics siedzi w a3a0_clean_tex.
                    elif suffix == ".mps":
                        mps_files.append(file)
    print(f"# Copied {copied_files_count}")
    print()

    for pdf_file in pdf_files:
        png_name = pdf_file.stem.replace("-eps-converted-to", "") + ".png"
        dest_path = PATH.FIGURES / png_name
        if convert_pdf_to_png(pdf_file, dest_path):
            converted_files_count += 1
            print(f"# Converted {dest_path}")
    for mps_file in mps_files:
        dest_path = PATH.FIGURES / (mps_file.stem + ".png")
        if convert_mps_to_png(mps_file, dest_path):
            converted_files_count += 1
            print(f"# Converted {dest_path}")
    print(f"# Converted {converted_files_count}")
    print()

    files_count = copied_files_count + converted_files_count
    print(f"# Prepared {files_count} images in {PATH.FIGURES}")


if __name__ == "__main__":
    prepare_images()
