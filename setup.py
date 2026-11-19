from setuptools import setup, find_packages

setup(
    name="route-resilience",
    version="3.0.0",
    description="Occlusion-Robust Road Extraction & 3D Grade-Separation Optimization",
    author="Route Resilience Contributors",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "pillow>=10.0.0",
        "pydantic>=2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "route-resilience-sim=run_simulation:main",
            "route-resilience-web=app:app"
        ]
    }
)
