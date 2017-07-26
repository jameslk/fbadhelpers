from setuptools import find_packages, setup

setup(
    name='fbadhelpers',
    version='0.1.0',
    packages=find_packages(),
    url='',
    license='MIT',
    author='James Koshigoe',
    author_email='james@jameskoshigoe.com',
    description='Helper utilities to simplify working with the Facebook Marketing API',
    install_requires=[
        'facebookads',
    ]
)
