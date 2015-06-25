from setuptools import setup, find_packages


setup(
    name='hist_compare_server',
    url='https://github.com/sklef/hist_compare',
    author='Dmitrii Smoliakov',
    version='0.1.0',
    author_email='dsmolyakov@yandex-team.ru',
    packages=find_packages(),
    description='Service for comparing particle histograms',
    install_requires=[
        "Flask>=0.10.1",
        "Jinja2>=2.7.3",
        "wsgiref>=0.1.2",
        "flask-admin>=1.1.0",
        "SQLAlchemy>=1.0.0b5",
        "requests>=2.0",
        "rootpy"
    ],
)