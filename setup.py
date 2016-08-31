from setuptools import setup

version = '0.0.1dev'

setup(
    name='journald-2-cloudwatch',
    version=version,
    author='林千里',
    author_email='lincheney@gmail.com',
    description='Send journald logs to AWS CloudWatch',
    url='https://github.com/lock8/journald-2-cloudwatch',
    packages=('jd2cw',),
    install_requires=['boto3'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['jd2cw = jd2cw:main'],
    }
)
