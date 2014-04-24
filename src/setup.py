from setuptools import setup

setup(name='mcstat',
      version='0.2.dev',
      description='Multicast statistics',
      author='Maciej Starzyk',
      author_email='mstarzyk@gmail.com',
      url='',
      # tests_require=['pytest'],
      packages=['mcstat', 'mcstat.tests'],
      entry_points={
          'console_scripts': [
              'mcstat = mcstat.main:main',
          ],
      }
      )
