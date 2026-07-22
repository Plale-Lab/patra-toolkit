from setuptools import setup

# read the contents of README
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name='patra-toolkit',
    version='0.3.0',
    packages=['tests', 'patra_toolkit'],
    package_data={'patra_toolkit': ['schema/schema.json']},
    include_package_data=True,
    url='https://github.com/Data-to-Insight-Center/patra-toolkit.git',
    license='BSD-3-Clause',
    author='Data to Insight Center',
    author_email='d2i@iu.edu',
    description='Toolkit for semi-automated modelcard creation for AI/ML models.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'jsonschema>4.18.5',
        'pandas>=2.0.0',
        'numpy>=1.23.5,<2.0.0',
        'requests>2.32.2',
        'setuptools>=65.0.0'        
    ],
    extras_require={
        'xai': ['shap~=0.46.0'],
        'fairness': ['fairlearn~=0.11.0']
    }
)
