from setuptools import setup

with open("README.md", "r") as rdme:
    desc = rdme.read()

setup(
    name = 'setisim',
    version = '0.0.1',
    url='https://github.com/avialxee/setsim',
    author='Avinash Kumar',
    author_email='avialxee@gmail.com',
    description='a python based package for Synthesis Imaging using CASA for SETI. Spectral Imaging for uGMRT data.',
    py_modules = ["setsim"],
    package_dir={'':'src'},
    classifiers=["Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.7",
                 "Programming Language :: Python :: 3.8",
                 "License :: OSI Approved :: BSD License",
                 "Intended Audience :: Science/Research",
                 ],
    long_description=desc,
    long_description_content_type = "text/markdown",
    install_requires=["astropy", "matplotlib",
                    "numpy", "casatasks", "casatools", "casadata"
                      ],
    extras_require = {
        "dev" : ["pytest>=3.7",
        ]
    }

)