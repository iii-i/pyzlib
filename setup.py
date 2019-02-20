import setuptools

with open('README.rst') as fp:
    long_description = fp.read()

setuptools.setup(
    name='pyzlib',
    version='0.1.6',
    author='Ilya Leoshkevich',
    author_email='iii@linux.ibm.com',
    description='Thin Python 3 wrapper around zlib',
    long_description=long_description,
    url='https://github.com/iii-i/pyzlib',
    packages=setuptools.find_packages(),
    classifiers=(
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
    ),
)
