from sigtools.modifiers import autokwoargs
from sigtools.wrappers import wrapper_decorator
from clize import run


def get_branch_object(repository, branch_name):
    return repository, branch_name


@wrapper_decorator(0, 'branch')
@autokwoargs
def with_branch(wrapped,
            repository='.', branch='master',
            *args, **kwargs):
    """Decorate with this so your function receives a branch object

    repository: A directory belonging to the repository to operate on

    branch: The name of the branch to operate on
    """
    return wrapped(
        *args, branch=get_branch_object(repository, branch), **kwargs)


@with_branch
@autokwoargs
def diff(branch=None):
    """Show the differences between the committed code and the working tree."""
    return "I'm different."


@with_branch
@autokwoargs
def commit(branch=None, *text):
    """Commit the changes.

    text: A message to store alongside the commit
    """
    return "All saved.: " + ' '.join(text)


@with_branch
@autokwoargs
def revert(branch=None):
    """Revert the changes made in the working tree."""
    return "There is no chip, John."


run(diff, commit, revert,
    description="A mockup version control system(like git, hg or bzr)")
