import setuptools

setuptools.setup(
    name = "gerrit_branch_workflow",
    version = "0.0.0",
    author = "Verily Life Sciences, LLC",
    description = "Tools for working with Gerrit and remote branches.",
    license = "BSD",
    keywords = "git gerrit branch",
    packages = ['gerrit_branch_workflow', 'tests'],
    include_package_data=True,
    install_requires=['GitPython'],
    entry_points={'console_scripts':['gbw = gerrit_branch_workflow.gbw:main']}
)
