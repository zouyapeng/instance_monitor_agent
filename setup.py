from setuptools import setup


setup(name='VMAgent',
      version='0.1.7',
      description='Openstack instance monitor agent',
      url='http://github.com/zouyapeng/instance_monitor_agent',
      author='Zouyapeng',
      author_email='zyp19901009@163.com',
      keywords='VMAgent OpenStack Instance Monitor',
      license='Apache',
      packages=['VMAgent'],
      install_requires=[
          'pymongo >= 3.2',
          'oslo.config >= 1.4.0'
      ],
      scripts=['bin/VMAgent', 'bin/VMAgent-stop'],
      data_files=[('/etc/VMAgent/', ['etc/VMAgent.conf'])],
      zip_safe=False
)