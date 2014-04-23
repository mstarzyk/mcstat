from distutils.core import setup

setup(name='mcstat',
      version='0.1',
      description='Multicast statistics',
      author='Maciej Starzyk',
      author_email='mstarzyk@gmail.com',
      url='',
      requires=['pytest'],
      packages=['mcstat', 'mctat.tests'],
      )
