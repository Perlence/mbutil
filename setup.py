from setuptools import setup

with open('README.md') as fp:
    README = fp.read()

setup(
    name='mbutil',
    version='0.1',
    author='Sviatoslav Abakumov',
    author_email='dust.harvesting@gmail.com',
    description='MusicBrainz utility for foobar2000',
    long_description=README,
    url='https://github.com/Perlence/mbutil',
    download_url='https://github.com/Perlence/mbutil/archive/master.zip',
    py_modules=['mbutil'],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'mbutil = mbutil:main',
        ],
    },
    install_requires=[
        'musicbrainzngs',
        'titlecase',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
    ]
)
