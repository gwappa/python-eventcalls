
import setuptools
from eventcalls import VERSION_STR

setuptools.setup(
    name='eventcalls',
    version=VERSION_STR,
    description='a threaded way for achieving event callbacks',
    url='',
    author='Keisuke Sehara',
    author_email='keisuke.sehara@gmail.com',
    license='MIT',
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        ],
    packages=['eventcalls',],
    entry_points={
        # nothing for the time being
    }
)
