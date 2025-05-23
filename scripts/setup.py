# setup.py (ejemplo básico para una app Tkinter)
import sys
from cx_Freeze import setup, Executable

# Archivos base (diferente para GUI en Windows)
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Para aplicaciones GUI en Windows, oculta la consola

# Opciones de construcción
build_exe_options = {
    "packages": ["tkinter", "mysql.connector", "os", "sys"], # Módulos a incluir explícitamente
    "includes": [], # Módulos que cx_Freeze podría no encontrar
    "excludes": [], # Módulos a excluir
    "include_files": [],
    # "zip_include_packages": ["*"], # Comprime paquetes en un zip
    # "zip_exclude_packages": [],
}

setup(
    name="Mantequilla",
    version="0.1",
    description="Descripción de tu aplicación de restaurante",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, icon="images.ico")] # Para Windows .ico, para Mac .icns
)