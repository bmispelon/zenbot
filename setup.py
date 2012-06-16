from distutils.core import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='zenbot',
    version='0.1',
    author='Baptiste Mispelon',
    author_email='bmispelon@gmail.com',
    packages=['zenbot'],
    url='https://github.com/bmispelon/zenbot',
    license='LICENSE.txt',
    description='A zen IRC bot.',
    long_description=long_description,
    requires=['Twisted'],
)
