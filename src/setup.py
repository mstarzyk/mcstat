from setuptools import setup

setup(name='mcstat',
      version='0.3.dev',
      description='Multicast statistics',
      author='Maciej Starzyk',
      author_email='mstarzyk@gmail.com',
      url='https://github.com/mstarzyk/mcstat',
      packages=['mcstat', 'mcstat.tests'],
      entry_points={
          'console_scripts': [
              'mcstat = mcstat.main:main',
          ],
      }
      )
