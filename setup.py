from setuptools import setup

setup(
    name="dpo-system",
    version="0.1.0",
    py_modules=["dpo_system"],
    packages=["dpo_system", "dpo_system.src"],
    entry_points={"console_scripts": ["dpo=dpo_system.cli:main"]},
)
