from cx_Freeze import setup, Executable
from utils_ import version

setup(
    name='Udemy Downlod',
    version=version,
    description='Salvando seus cursos localmente você assiste quando bem desejar!',
    executables=[Executable(
        script=r'./udemy_download.py',
        base=None,
        icon=r'./bin/favicon.ico'
    )],
    options={
        'build_exe': {
            'include_files': [],
            'excludes': [],
            'include_msvcr': True,
        }
    }
)

# python setup.py build
