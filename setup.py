from setuptools import setup

setup(
    name='shotty',
    version='0.1',
    author='Dennis Vriend',
    author_email='dnvriend@gmail.com',
    description="a tool for managing ec2 snapshots",
    licence='Apache 2.0',
    packages=['shotty'],
    url="http://foo.bar",
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',
)