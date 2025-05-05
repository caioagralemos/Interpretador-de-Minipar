from cx_Freeze import Executable, setup

# Caminho para o arquivo __main__.py
executables = [
    Executable("minipar/__main__.py", base="Console", target_name="minipar")
]

# Configuração do setup
setup(
    name="MiniPar",
    version="0.1",
    description="Um interpretador para a linguagem MiniPar",
    options={
        'build_exe': {
            'include_files': [],
        }
    },
    executables=executables,
)
