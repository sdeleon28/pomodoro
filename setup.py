from setuptools import setup

setup(
    name='pomodoro',
    version='1.0',
    py_modules='pomodoro',
    install_requires=['click'],
    entry_points='''
        [console_scripts]
        pom=pomodoro:cli
    ''',
)
