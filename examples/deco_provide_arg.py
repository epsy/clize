from sigtools.wrappers import decorator
from clize import run


def get_branch_object(repository, branch_name):
    return repository, branch_name


@decorator
def with_branch(wrapped, *args, repository='.', branch='master', **kwargs):
    """Decorate with this so your function receives a branch object

    :param repository: A directory belonging to the repository to operate on
    :param branch: The name of the branch to operate on
    """
    return wrapped(*args, branch=get_branch_object(repository, branch), **kwargs)


@with_branch
def diff(*, branch=None):
    """Show the differences between the committed code and the working tree."""
    return "I'm different."


@with_branch
def commit(*text, branch=None):
    """Commit the changes.

    :param text: A message to store alongside the commit
    """
    return "All saved.: " + ' '.join(text)


@with_branch
def revert(*, branch=None):
    """Revert the changes made in the working tree."""
    return "All changes reverted!"


run(diff, commit, revert,
    description="A mockup version control system(like git, hg or bzr)")
