import argparse
import os
import sys

import git

from . import git_repository
from . import gerrit_utils


def new_command(repo_path, branch_name):
    _forbid_suspicious_branch_names(branch_name)
    repo = git_repository.GitRepository(repo_path)
    new_branch = repo.create_local_branch(branch_name)
    try:
        repo.checkout_branch(branch_name)
        try:
            repo.create_remote_tracking_branch(branch_name)
        except:
            repo.delete_local_branch(branch_name)
            raise
    except:
        repo.delete_local_branch(branch_name)
        raise

    return True


def rm_command(repo_path, branch_name):
    _forbid_suspicious_branch_names(branch_name)
    repo = git_repository.GitRepository(repo_path)
    repo.checkout_branch('master')
    repo.delete_remote_tracking_branch(branch_name)
    repo.delete_local_branch(branch_name, force=True)
    return True


def review_command(repo_path, ancestor_branch_name, message):
    repo = git_repository.GitRepository(repo_path)
    if repo.untracked_files() or repo.is_dirty():
        print('repository has untracked or uncommitted files, aborting.')
        return False

    working_branch_name = repo.current_branch_name()
    if working_branch_name == 'master':
        print('can\'t start a review from master branch, aborting.')
        return False

    staging_branch_name = repo.current_branch_name() + '-gbw-gerrit-staging'
    staging_branch = repo.create_local_branch(staging_branch_name)

    try:
        repo.checkout_branch(staging_branch_name)
        staging_branch_fork_point = repo.merge_base(ancestor_branch_name)
        staging_branch_commits = repo.get_branch_commits(ancestor_branch_name)
        gerrit_commit_msg = gerrit_utils.flattened_commit_message_from_commits(
            staging_branch_commits)
        repo.soft_reset_to_commit(staging_branch_fork_point[0])
        repo.commit(gerrit_commit_msg)
        gerrit_utils.push_branch_for_review(repo, staging_branch_name)

    finally:
        repo.checkout_branch(working_branch_name)
        repo.delete_local_branch(staging_branch_name, force=True)


def _forbid_suspicious_branch_names(branch_name):
    if branch_name in [
            '', 'master', 'origin', 'upstream', 'remote', 'tags', 'release'
    ]:
        raise ValueError(
            'Suspicious branch name "{}" requested, confirm by forcing.'.format(
                branch_name))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tool for working with Gerrit and remote branches.'
        ' Run with "{command} -h" for command-specific help.')

    command_subparsers = parser.add_subparsers(
        help='available commands', dest='command')

    #### new command

    new_command_subparser = command_subparsers.add_parser(
        'new', help='create a new local branch and remote tracking branch')
    new_command_subparser.add_argument(
        'branch',
        help='name of the branch to create locally and and track on origin')

    #### rm command

    rm_command_subparser = command_subparsers.add_parser(
        'rm', help='delete a local branch and its remote tracking branch')
    rm_command_subparser.add_argument(
        'branch', help='name of the branch to delete locally and on origin')

    rm_command_subparser.add_argument(
        '-f',
        '--force',
        help='delete even if the branch hasn\'t been submitted to gerrit.')

    #### review command

    review_command_subparser = command_subparsers.add_parser(
        'review',
        help='create or update a gerrit review from the current branch.',
        epilog='All commit messages in the review branch will be '
        'concatenated into the review description.')

    review_command_subparser.add_argument(
        '-b',
        '--ancestor-branch',
        default='master',
        help=
        'branch from which the current review branch forked. (default: master)')

    review_command_subparser.add_argument(
        '-m',
        '--message',
        default='',
        help='commit message to preface the gerrit review with')

    return parser.parse_args()


def main():
    cwd = os.getcwd()

    args = parse_args()
    if not args.command:
        print('command required, run with "-h" for help.')
        return False

    if args.command == 'new':
        success = new_command(cwd, args.branch)
    elif args.command == 'rm':
        success = rm_command(cwd, args.branch)
    elif args.command == 'review':
        success = review_command(cwd, args.ancestor_branch, args.message)
    else:
        raise ValueError('unexpected command "{}"'.format(args.command))

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
