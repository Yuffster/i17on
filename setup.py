from setuptools import setup, find_packages

VERSION = '0.1.1'

config = {
    'description': "An intranationalization engine for dynamic Markdown documents.",
    'author': "Michelle Steigerwalt",
    'author_email': "msteigerwalt@gmail.com",
    'url': 'http://i17on.com',
    'version': VERSION,
    'packages': find_packages(exclude=["tests"]),
    'entry_points': {
        "console_scripts": [
            'i17on = i17on.__main__:main'
        ]
    },
    'name': 'i17on',
    'test_suite': 'nose.collector',
    'zip_safe': False
}

setup(**config)
