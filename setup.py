from setuptools import setup

# read the contents of README
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name='patra-toolkit',
    version='1.0.0',
    packages=['tests', 'patra_toolkit'],
    package_data={'patra_toolkit': ['schema/schema.json']},
    include_package_data=True,
    url='https://github.com/Plale-Lab/patra-toolkit.git',
    license='BSD-3-Clause',
    author='Data to Insight Center',
    author_email='d2i@iu.edu',
    description='Toolkit for semi-automated modelcard creation for AI/ML models.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'jsonschema>4.18.5',
        'pandas>=2.0.0',
        'requests>2.32.2',
        'urllib3>=2.7.0',
        'setuptools>=65.0.0'
    ],
    extras_require={
        'xai': ['shap~=0.46.0'],
        'fairness': ['fairlearn~=0.11.0'],
        'experiments': [
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            'pillow>=9.0.0',
            'confluent-kafka>=2.0.0',
        ]
    }
)
