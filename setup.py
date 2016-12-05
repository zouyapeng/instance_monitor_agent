from setuptools import setup

setup(name='VMAgent',
      version='0.1',
      description='Openstack instance monitor agent',
      url='http://github.com/zouyapeng/instance_monitor_agent',
      author='Zouyapeng',
      author_email='zyp19901009@163.com',
      keywords='VMAgent OpenStack Instance Monitor',
      license='Apache',
      packages=['VMAgent'],
      install_requires=[
          'pymongo==3.4.0',
      ],
      scripts=['bin/VMAgent'],
      data_files=[('/etc/VMAgent/', ['VMAgent.conf'])],
      zip_safe=False
)