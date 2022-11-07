from setuptools import setup


def readme():
    """
    grab and return contents of README.md for use in long description
    """
    with open('README.md') as f:
        return f.read()


lic_class = ('License :: OSI Approved :: GNU Affero General Public License v3'
             ' or later (AGPLv3+)')


setup(name='smol_k8s_lab',
      description='bootstrap simple projects on kubernetes with kind and k3s',
      long_description=readme(),
      long_description_content_type='text/markdown',
      classifiers=['Development Status :: 3 - Alpha'
                   'Programming Language :: Python :: 3.10'
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX :: Linux',
                   'Intended Audience :: End Users/Desktop',
                   'Topic :: System :: Installation/Setup',
                   lic_class],
      python_requires='>3.10',
      keywords='kubernetes homelab kind k3s k8s',
      version='0.8.17_a0',
      project_urls={
          'Documentation': 'https://jessebot.github.io/smol_k8s_lab',
          'Source': 'http://github.com/jessebot/smol_k8s_lab',
          'Tracker': 'http://github.com/jessebot/smol_k8s_lab/issues'
          },
      author='Jesse Hitch',
      author_email='jessebot@linux.com',
      license='GPL version 3 or later',
      packages=['smol_k8s_lab'],
      install_requires=['PyYAML', 'rich', 'click', 'bcrypt', 'requests'],
      data_files=[('config', ['config/config_sample.yml'])],
      entry_points={'console_scripts': ['smol-k8s-lab = smol_k8s_lab:main']},
      include_package_data=True,
      zip_safe=False)
