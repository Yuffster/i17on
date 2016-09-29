from setuptools import setup, find_packages

config = {
    'description': "An intranationalization engine for dynamic Markdown documents.",
    'author': "Michelle Steigerwalt",
    'url': 'http://i17on.com',
    'version': '0.1',
    'packages': find_packages(exclude=["tests"]),
    'entry_points': {
        "console_scripts": [
            'i17on = i17on.__main__'
        ]
    },
    'name': 'i17on',
    'test_suite': 'nose.collector',
    'zip_safe': False
}

setup(**config)